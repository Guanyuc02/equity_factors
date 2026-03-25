import pandas as pd
import numpy as np
import datetime as dt
import wrds
#import psycopg2 
import matplotlib.pyplot as plt
from dateutil.relativedelta import *
from pandas.tseries.offsets import *
from scipy import stats
from pathlib import Path
import warnings

START_DATE = pd.Timestamp('1976-07-30')

conn = wrds.Connection()

###################
# Compustat Block #
###################
sql = """
WITH f AS (
  SELECT gvkey, datadate, at, act, lct, pstkl, txditc, pstkrv, seq, pstk, sich
  FROM comp.funda
  WHERE indfmt='INDL' AND datafmt='STD' AND popsrc='D' AND consol='C'
    AND datadate >= '1975-01-01'
)
SELECT f.gvkey,
       f.datadate,
       f.at, f.act, f.lct, f.pstkl, f.txditc, f.pstkrv, f.seq, f.pstk,
       COALESCE(f.sich, NULLIF(c.sic,'')::int) AS sic
FROM f
LEFT JOIN comp.company c USING (gvkey)
"""
comp = pd.read_sql(sql, con=conn.engine, parse_dates=['datadate'])
comp['year'] = comp['datadate'].dt.year
comp['sic'] = pd.to_numeric(comp['sic'], errors='coerce').astype('Int64')

# create preferred stock
comp['ps']=np.where(comp['pstkrv'].isnull(), comp['pstkl'], comp['pstkrv'])
comp['ps']=np.where(comp['ps'].isnull(),comp['pstk'], comp['ps'])
comp['ps']=np.where(comp['ps'].isnull(),0,comp['ps'])
comp['txditc']=comp['txditc'].fillna(0)

# create book equity
comp['be']=comp['seq']+comp['txditc']-comp['ps']
comp['be']=np.where(comp['be']>0, comp['be'], np.nan)

# current ratio from prior fiscal year-end
comp['currat'] = np.where(comp['lct'] > 0, comp['act'] / comp['lct'], np.nan)

# number of years in Compustat
comp=comp.sort_values(by=['gvkey','datadate'])
comp['count']=comp.groupby(['gvkey']).cumcount()

comp=comp[['gvkey','datadate','year','be','currat','count','sic']]

###################
# CRSP Block      #
###################
# msf_v2 has no shrcd. Join monthly names to get shrcd and exchcd.
crsp_m = conn.raw_sql("""
    SELECT
        a.permno,
        a.permco,
        a.mthcaldt,
        n.shrcd,
        n.exchcd,
        a.issuertype,
        a.securitytype,
        a.securitysubtype,
        a.sharetype,
        a.usincflg,
        a.primaryexch,
        a.conditionaltype,
        a.tradingstatusflg,
        a.mthret,
        a.mthretx,
        a.shrout,
        a.mthprc
    FROM crsp.msf_v2 AS a
    LEFT JOIN crsp.msenames AS n
      ON a.permno = n.permno
     AND a.mthcaldt BETWEEN n.namedt AND COALESCE(n.nameendt, DATE '9999-12-31')
    WHERE a.mthcaldt BETWEEN DATE '1975-01-01' AND DATE '2024-12-31'
""", date_cols=['mthcaldt'])

### Select common stock universe
# - equivalent to legacy code shrcd = 10 or 11
crsp_m = crsp_m.query("shrcd in [10, 11]")
crsp_m.shape

### Select stocks traded on NYSE, AMEX and NASDAQ
# - equivalent to legacy code exchcd = 1, 2 or 3
cols = set(crsp_m.columns)
if 'exchcd' in cols:
    crsp_m = crsp_m[crsp_m['exchcd'].isin([1, 2, 3])]
else:
    crsp_m = crsp_m[crsp_m['primaryexch'].isin(['N', 'A', 'Q'])]
crsp_m.shape

# change variable format to int
crsp_m[['permco','permno']]=crsp_m[['permco','permno']].astype(int)

# Line up date to be end of month
crsp_m['jdate'] = crsp_m['mthcaldt']

# Canonical month calendar: CRSP last trading day per month
calmap = (
    crsp_m[['mthcaldt']]
      .dropna()
      .assign(cal_mend=lambda d: d['mthcaldt'] + MonthEnd(0),
              ym=lambda d: d['mthcaldt'].dt.to_period('M'))
      .groupby('ym', as_index=False)
      .agg(ltrd=('mthcaldt', 'max'), cal_mend=('cal_mend', 'max'))
      .sort_values('ltrd')
)
month_index = calmap['ltrd'].copy()
month_index = month_index[month_index >= START_DATE]

### No need to add delisting return in the new CIZ CRSP format
# - last trading return and price prior to delisting are already part of the time series output

# calculate market equity
crsp = crsp_m.copy()
crsp['mthret'] = crsp['mthret'].fillna(0)
crsp['mthretx'] = crsp['mthretx'].fillna(0)
# CRSP PRC can be negative when it is a bid/ask average. Use abs(price).
# SHROUT is in thousands.
crsp['me'] = crsp['mthprc'].abs() * crsp['shrout']
crsp=crsp.drop(['mthprc','shrout'], axis=1)
crsp=crsp.sort_values(by=['jdate','permco','me'])

### Aggregate Market Cap ###
# sum of me across different permno belonging to same permco a given date
crsp_summe = crsp.groupby(['jdate','permco'])['me'].sum().reset_index()

# largest mktcap within a permco/date
crsp_maxme = crsp.groupby(['jdate','permco'])['me'].max().reset_index()

# join by jdate/maxme to find the permno
crsp1=pd.merge(crsp, crsp_maxme, how='inner', on=['jdate','permco','me'])

# drop me column and replace with the sum me
crsp1=crsp1.drop(['me'], axis=1)

# join with sum of me to get the correct market cap info
crsp2=pd.merge(crsp1, crsp_summe, how='inner', on=['jdate','permco'])

# sort by permno and date and also drop duplicates
crsp2=crsp2.sort_values(by=['permno','jdate']).drop_duplicates()

# keep December market cap
crsp2['year']=crsp2['jdate'].dt.year
crsp2['month']=crsp2['jdate'].dt.month
decme=crsp2[crsp2['month']==12].copy()
decme=decme[['permno','mthcaldt','jdate','me','year']].rename(columns={'me':'dec_me'})

### July to June dates
crsp2['ffdate']=crsp2['jdate']+MonthEnd(-6)
crsp2['ffyear']=crsp2['ffdate'].dt.year
crsp2['ffmonth']=crsp2['ffdate'].dt.month
crsp2['1+retx']=1+crsp2['mthretx']
crsp2=crsp2.sort_values(by=['permno','mthcaldt'])

# cumret by stock
crsp2['cumretx']=crsp2.groupby(['permno','ffyear'])['1+retx'].cumprod()

# lag cumret
crsp2['lcumretx']=crsp2.groupby(['permno'])['cumretx'].shift(1)

# lag market cap
crsp2['lme']=crsp2.groupby(['permno'])['me'].shift(1)

# if first permno then use me/(1+retx) to replace the missing value
crsp2['count']=crsp2.groupby(['permno']).cumcount()
crsp2['lme']=np.where(crsp2['count']==0, crsp2['me']/crsp2['1+retx'], crsp2['lme'])

# baseline me
mebase=crsp2[crsp2['ffmonth']==1][['permno','ffyear', 'lme']].rename(columns={'lme':'mebase'})

# merge result back together
crsp3=pd.merge(crsp2, mebase, how='left', on=['permno','ffyear'])
crsp3['wt']=np.where(crsp3['ffmonth']==1, crsp3['lme'], crsp3['mebase']*crsp3['lcumretx'])

decme['year']=decme['year']+1
decme=decme[['permno','year','dec_me']]

# Info as of June (CRSP dated on last trading day but we add a month key for joining)
crsp3_jun = crsp3[crsp3['month'] == 6].copy()
crsp_jun = pd.merge(crsp3_jun, decme, how='inner', on=['permno','year'])
crsp_jun = crsp_jun[['permno','mthcaldt','jdate','ffyear','sharetype','securitytype','securitysubtype',
                     'usincflg','issuertype','primaryexch','conditionaltype','tradingstatusflg',
                     'mthret','me','wt','cumretx','mebase','lme','dec_me']].copy()
# month key for join, preserves CRSP last-trading-day 'jdate' for outputs
crsp_jun['ym'] = crsp_jun['jdate'].dt.to_period('M')
crsp_jun = crsp_jun.sort_values(['permno','jdate']).drop_duplicates()

#######################
# CCM Block           #
#######################
ccm=conn.raw_sql("""
                  select gvkey, lpermno as permno, linktype, linkprim, 
                  linkdt, linkenddt
                  from crsp.ccmxpf_linktable
                  where substr(linktype,1,1)='L'
                  and (linkprim ='C' or linkprim='P')
                  """, date_cols=['linkdt', 'linkenddt'])

# if linkenddt is missing then set to today date
ccm['linkenddt']=ccm['linkenddt'].fillna(pd.to_datetime('today'))

ccm1=pd.merge(comp[['gvkey','datadate','be','currat','count','sic']],ccm,how='left',on=['gvkey'])
ccm1['yearend']=ccm1['datadate']+YearEnd(0)
ccm1['jdate']=ccm1['yearend']+MonthEnd(6)  # calendar June 30 anchor

# set link date bounds
ccm2 = ccm1[(ccm1['jdate']>=ccm1['linkdt'])&(ccm1['jdate']<=ccm1['linkenddt'])].copy()
# month key (calendar month end); one record per permno×month after tie-break on latest accounting date
ccm2['ym'] = ccm2['jdate'].dt.to_period('M')
# enforce FF93 vintage: last fiscal year-end in calendar t-1 for June of year t
ccm2 = ccm2[ccm2['datadate'].dt.year == (ccm2['ym'].dt.year - 1)]
ccm2 = (ccm2
        .sort_values(['permno','ym','datadate'])
        .drop_duplicates(['permno','ym'], keep='last')
        [['gvkey','permno','datadate','yearend','jdate','ym','be','currat','count','sic']])

# link comp and crsp using month key, keep CRSP last-trading-day date for downstream use
ccm_jun = pd.merge(crsp_jun,
                   ccm2.rename(columns={'jdate':'ccm_cal_mend'}),
                   how='inner',
                   on=['permno','ym'])
# standardize 'jdate' to the CRSP last-trading-day stamp expected by the rest of the pipeline
ccm_jun = ccm_jun.rename(columns={'jdate':'jdate_crsp'})
ccm_jun['jdate'] = ccm_jun['jdate_crsp']
ccm_jun = ccm_jun.drop(columns=['jdate_crsp'])
ccm_jun = ccm_jun[ccm_jun['dec_me'] > 0]
ccm_jun['beme'] = (ccm_jun['be'] * 1000) / ccm_jun['dec_me']
ccm_jun = ccm_jun.replace([np.inf, -np.inf], np.nan).dropna(subset=['beme'])

# Exclude financials before breakpoints and portfolio formation
ccm_jun = ccm_jun[~((ccm_jun['sic'] >= 6000) & (ccm_jun['sic'] <= 6999))]

## NYSE samples for breakpoints
# Size breakpoint uses June ME (end of June of year t)
nyse_size = ccm_jun[(ccm_jun['primaryexch'] == 'N') & (ccm_jun['me'] > 0)]
# B/M breakpoints unchanged; enforce positive December ME for robustness (BE/ME uses Dec of t-1).
nyse_bm_samp = ccm_jun[
    (ccm_jun['primaryexch'] == 'N') &
    (ccm_jun['beme'] > 0) &
    (ccm_jun['dec_me'] > 0)
]

# size breakpoint from June ME
nyse_sz = (
    nyse_size.groupby('jdate')['me']
    .median()
    .to_frame()
    .reset_index()
    .rename(columns={'me': 'sizemedn_jun'})
)

# Explicit NYSE empirical breakpoints per month
nyse_bm = (
    nyse_bm_samp.groupby('jdate')['beme']
    .quantile([0.3, 0.7], interpolation='nearest')
    .unstack()
    .reset_index()
    .rename(columns={0.3: 'bm30', 0.7: 'bm70'})
)

nyse_breaks = pd.merge(nyse_sz, nyse_bm, how='inner', on='jdate')

# NYSE empirical breakpoints for current ratio
nyse_cr_samp = ccm_jun[
    (ccm_jun['primaryexch'] == 'N') &
    (ccm_jun['dec_me'] > 0) &
    (ccm_jun['currat'].notna())
]
nyse_cr = (
    nyse_cr_samp.groupby('jdate')['currat']
    .quantile([0.3, 0.7], interpolation='nearest')
    .unstack()
    .reset_index()
    .rename(columns={0.3: 'cr30', 0.7: 'cr70'})
)

# join back size and beme breakdown
ccm1_jun = pd.merge(ccm_jun, nyse_breaks, how='left', on=['jdate'])
ccm1_jun = pd.merge(ccm1_jun, nyse_cr, how='left', on=['jdate'])

# remove unused sz_bucket helper 

def bm_bucket(row):
    if 0<=row['beme']<=row['bm30']:
        value = 'L'
    elif row['beme']<=row['bm70']:
        value='M'
    elif row['beme']>row['bm70']:
        value='H'
    else:
        value=''
    return value

# base validity mask (handle pd.NA safely)
m_valid = (ccm1_jun['beme'].gt(0) & ccm1_jun['me'].gt(0) & ccm1_jun['dec_me'].gt(0)).fillna(False)

# ---- size portfolio from June ME: S if me <= sizemedn_jun else B ----
ccm1_jun['szport'] = ''
mask_sz = m_valid & ccm1_jun[['me', 'sizemedn_jun']].notna().all(axis=1)
ccm1_jun.loc[mask_sz, 'szport'] = np.where(
    ccm1_jun.loc[mask_sz, 'me'] <= ccm1_jun.loc[mask_sz, 'sizemedn_jun'],
    'S', 'B'
)

# ---- book-to-market portfolio: L/M/H via precomputed breakpoints bm30, bm70 ----
ccm1_jun['bmport'] = ''
mask_bm = m_valid & ccm1_jun[['beme', 'bm30', 'bm70']].notna().all(axis=1)
bm = ccm1_jun.loc[mask_bm, 'beme']
bm30 = ccm1_jun.loc[mask_bm, 'bm30']
bm70 = ccm1_jun.loc[mask_bm, 'bm70']

ccm1_jun.loc[mask_bm, 'bmport'] = np.select(
    [bm <= bm30, bm <= bm70, bm > bm70],
    ['L', 'M', 'H'],
    default=''
)

# ---- current ratio portfolio: L/M/H via precomputed breakpoints cr30, cr70 ----
ccm1_jun['crport'] = ''
mask_cr = m_valid & ccm1_jun[['currat', 'cr30', 'cr70']].notna().all(axis=1)
cr = ccm1_jun.loc[mask_cr, 'currat']
cr30 = ccm1_jun.loc[mask_cr, 'cr30']
cr70 = ccm1_jun.loc[mask_cr, 'cr70']
ccm1_jun.loc[mask_cr, 'crport'] = np.select(
    [cr <= cr30, cr <= cr70, cr > cr70],
    ['L', 'M', 'H'],
    default=''
)
ccm1_jun['poscr'] = (ccm1_jun['currat'].notna()).astype('int8')
ccm1_jun['nonmiss_cr'] = (ccm1_jun['crport'] != '').astype('int8')

# ---- indicators ----
ccm1_jun['posbm'] = m_valid.astype('int8')                   
ccm1_jun['nonmissport'] = (ccm1_jun['bmport'] != '').astype('int8')

# store portfolio assignment as of June

june = (
    ccm1_jun[['permno','mthcaldt','jdate','bmport','szport','posbm','nonmissport',
              'crport','poscr','nonmiss_cr']]
    .copy()
)
june.loc[:, 'ffyear'] = june['jdate'].dt.year

# merge back with monthly records
crsp3 = crsp3[['mthcaldt','permno', 'sharetype', 'securitytype', 'securitysubtype', 'usincflg', 'issuertype', \
               'primaryexch', 'conditionaltype', 'tradingstatusflg', \
               'mthret', 'me','wt','cumretx','ffyear','jdate']]
ccm3=pd.merge(crsp3, 
        june[['permno','ffyear','szport','bmport','posbm','nonmissport',
              'crport','poscr','nonmiss_cr']], how='left', on=['permno','ffyear'])

# keeping only records that meet the criteria
ccm4=ccm3[(ccm3['wt']>0)& (ccm3['posbm']==1) & (ccm3['nonmissport']==1)]

############################
# Form Fama French Factors #
############################

# function to calculate value weighted return
def wavg(group, avg_name, weight_name):
    d = group[avg_name]
    w = group[weight_name]
    try:
        return (d * w).sum() / w.sum()
    except ZeroDivisionError:
        return np.nan
    
# value-weighted return
_tmp = ccm4.assign(wx=ccm4['mthret'] * ccm4['wt'])
vwret = (
    _tmp.groupby(['jdate','szport','bmport'], as_index=False)
        .agg(wx_sum=('wx','sum'), w_sum=('wt','sum'))
)
vwret['vwret'] = np.where(vwret['w_sum'] > 0, vwret['wx_sum'] / vwret['w_sum'], np.nan)
vwret = vwret.drop(columns=['wx_sum','w_sum'])
vwret['sbport']=vwret['szport']+vwret['bmport']

# firm count
vwret_n=ccm4.groupby(['jdate','szport','bmport'])['mthret'].count().reset_index().rename(columns={'mthret':'n_firms'})
vwret_n['sbport']=vwret_n['szport']+vwret_n['bmport']

# transpose to jdate × {SL,SM,SH,BL,BM,BH}
ff_p = vwret.pivot(index='jdate', columns='sbport', values='vwret')

# compute HML and SMB only
ff_factors = (
    ff_p[['SL','SM','SH','BL','BM','BH']].assign(
        WH=lambda d: (d['BH'] + d['SH']) / 2,
        WL=lambda d: (d['BL'] + d['SL']) / 2,
        HML=lambda d: d['WH'] - d['WL'],
        WB=lambda d: (d['BL'] + d['BM'] + d['BH']) / 3,
        WS=lambda d: (d['SL'] + d['SM'] + d['SH']) / 3,
        SMB=lambda d: d['WS'] - d['WB']
    )[['HML','SMB']]
    .reset_index()
    .rename(columns={'jdate':'date'})
)

# currat factor using 2x3 sorts on size × current ratio
ccm4_cr = ccm3[(ccm3['wt']>0) & (ccm3['poscr']==1) & (ccm3['nonmiss_cr']==1)].copy()
_tmp_cr = ccm4_cr.assign(wx=ccm4_cr['mthret'] * ccm4_cr['wt'])
vwret_cr = (
    _tmp_cr.groupby(['jdate','szport','crport'], as_index=False)
           .agg(wx_sum=('wx','sum'), w_sum=('wt','sum'))
)
vwret_cr['vwret'] = np.where(vwret_cr['w_sum'] > 0, vwret_cr['wx_sum'] / vwret_cr['w_sum'], np.nan)
vwret_cr = vwret_cr.drop(columns=['wx_sum','w_sum'])
vwret_cr['scport'] = vwret_cr['szport'] + vwret_cr['crport']
cr_p = vwret_cr.pivot(index='jdate', columns='scport', values='vwret')
currat_series = (
    cr_p[['SL','SM','SH','BL','BM','BH']].assign(
        WH=lambda d: (d['BH'] + d['SH']) / 2,
        WL=lambda d: (d['BL'] + d['SL']) / 2,
        currat=lambda d: d['WL'] - d['WH']
    )[['currat']]
    .reset_index()
    .rename(columns={'jdate':'date'})
)

# ensure full monthly coverage on CRSP last trading day calendar
ff_factors = (
    ff_factors.set_index('date')
              .reindex(month_index)
              .rename_axis('date')
              .reset_index()
)
currat_series = (
    currat_series.set_index('date')
                 .reindex(month_index)
                 .rename_axis('date')
                 .reset_index()
)

# merge in currat
ff_factors = ff_factors.merge(currat_series, on='date', how='left')
ff_factors = ff_factors[['date','SMB','HML','currat']]

############################
# Persist factor series    #
############################
outdir = Path("out_ff3")
outdir.mkdir(parents=True, exist_ok=True)
ff_csv = outdir / "ff_factors.csv"
ff_xlsx = outdir / "ff_factors.xlsx"

ff_factors.to_csv(ff_csv, index=False)
try:
    ff_factors.to_excel(ff_xlsx, index=False)
except Exception as e:
    warnings.warn(f"Excel export failed: {e}. CSV was saved to {ff_csv}")

# Assert no missing months in the saved range
_ym = ff_factors['date'].dt.to_period('M')
_expected = pd.PeriodIndex(month_index.dt.to_period('M'))
_missing = [p for p in _expected.astype(str) if p not in set(_ym.astype(str))]
if _missing:
    warnings.warn(f"Month coverage gap after reindex: {len(_missing)} months still missing: { _missing[:12] } ...")
