### Appendix_factors

| ID | Description | Year.pub | Year.end | Avg.Ret. | Ann.SR | Reference | Abbreviation | Implementation | Replication Progress | Name in OpenSourceAssetPricing.py | Name in OpenSourceAssetPricing csv |
| :--- | :----------- | :-------- | :-------- | :-------- | :------ | :--------- | :------------ | :-------------- | :-------------------- | :--------------------------------- | :---------------------------------- |
| 1 | Excess Market Return | 1972 | 1965 | 0.0064 | 0.506 | Jensen, Black, and Scholes (1972) | MktRf | Publicly sourced replicated | Done |  |  |
| 2 | Market Beta | 1973 | 1968 | −0.08% | −5.4% | Fama and MacBeth (1973) | beta |  |  | Beta | Beta |
| 3 | Earnings to price | 1977 | 1971 | 0.0028 | 0.297 | Basu (1977) | ep | data_rawq['ep'] = data_rawq['ibq4']/data_rawq['me'] | done | EP | EP |
| 4 | Dividend to price | 1979 | 1977 | 0.0001 | 0.006 | Litzenberger and Ramaswamy (1979) | dy | dvt/mve_f |  | DivYieldST | DivYieldST |
| 5 | Unexpected quarterly earnings | 1982 | 1980 | 0.0012 | 0.263 | Rendleman, Jones, and Latane (1982) | sue |  |  |  |  |
| 6 | Share price | 1982 | 1978 | 0.0002 | 0.022 | Miller and Scholes (1982) | pps | log(lag(prc)) | Done |  |  |
| 7 | Long-Term Reversal | 1985 | 1982 | 0.0034 | 0.363 | Bondt and Thaler (1985) | LTR | Publicly sourced replicated | Done | LRreversal | LRreversal |
| 8 | Leverage | 1988 | 1981 | 0.0021 | 0.243 | Bhandari (1988) | lev | data_rawq['lev'] = data_rawq['ltq']/data_rawq['me'] | Done | Leverage | Leverage |
| 9 | Cash ﬂow to debt | 1989 | 1984 | −0.09% | −17.0% | Ou and Penman (1989) | cashdebt | data_rawq['cashdebt'] = (ttm4('ibq', data_rawq) + ttm4('dpq', data_rawq))/((data_rawq['ltq']+data_rawq['ltq_l4'])/2) | Done |  |  |
| 10 | Current ratio | 1989 | 1984 | 0.0006 | 0.077 | Ou and Penman (1989) | currat | act/lct | Done |  |  |
| 11 | % change in current ratio | 1989 | 1984 | 0 | 0.005 | Ou and Penman (1989) | pchcurrat | ((act/lct)-(lag(act)/lag(lct)))/(lag(act)/lag(lct)) | Done |  |  |
| 12 | % change in quick ratio | 1989 | 1984 | −0.04% | −11.9% | Ou and Penman (1989) | pchquick | ( (act-invt)/lct - (lag(act)-lag(invt))/lag(lct) )/ ( ( lag(act)-lag(invt) )/lag(lct) ) | Done |  |  |
| 13 | % change sales-to-inventory | 1989 | 1984 | 0.0017 | 0.462 | Ou and Penman (1989) | pchsaleinv | ( (sale/invt)-(lag(sale)/lag(invt)) ) / (lag(sale)/lag(invt)) | Done |  |  |
| 14 | Quick ratio | 1989 | 1984 | −0.02% | −2.9% | Ou and Penman (1989) | quick | (act-invt)/lct | Done |  |  |
| 15 | Sales to cash | 1989 | 1984 | 0.0001 | 0.015 | Ou and Penman (1989) | salecash | sale/che | Done |  |  |
| 16 | Sales to inventory | 1989 | 1984 | 0.0009 | 0.161 | Ou and Penman (1989) | saleinv | sale/invt | Done |  |  |
| 17 | Sales to receivables | 1989 | 1984 | 0.0014 | 0.228 | Ou and Penman (1989) | salerec | sale/rect | Done |  |  |
| 18 | Bid-ask spread | 1989 | 1979 | −0.04% | −3.3% | Amihud and Mendelson (1989) | baspread |  |  | BidAskSpread | BidAskSpread |
| 19 | Depreciation/PP&E | 1992 | 1988 | 0.0011 | 0.121 | Holthausen and Larcker (1992) | depr | data_rawq['depr'] = ttm4('dpq', data_rawq)/data_rawq['ppentq'] | Done |  |  |
| 20 | % change in depreciation | 1992 | 1988 | 0.0008 | 0.231 | Holthausen and Larcker (1992) | pchdepr | ((dp/ppent)-(lag(dp)/lag(ppent)))/(lag(dp)/lag(ppent)) | Done |  |  |
| 21 | Small Minus Big | 1993 | 1991 | 0.0021 | 0.245 | Fama and French (1993) | SMB | Publicly sourced replicated | Done |  |  |
| 22 | High Minus Low | 1993 | 1991 | 0.0028 | 0.343 | Fama and French (1993) | HML | Publicly sourced replicated | Done |  |  |
| 23 | Short-Term Reversal | 1993 | 1989 | 0.0015 | 0.217 | Jegadeesh and Titman (1993) | STR | Publicly sourced replicated | Done |  |  |
| 24 | 6-month momentum | 1993 | 1989 | 0.0021 | 0.278 | Jegadeesh and Titman (1993) (Continued) Taming the Factor Zoo 1361 | mom6m | crsp_mom['mom6m'] = mom(1, 6, crsp_mom) |  | Mom6m | Mom6m |
| 25 | 36-month momentum | 1993 | 1989 | 0.0009 | 0.134 | Jegadeesh and Titman (1993) | mom36m | crsp_mom['mom36m'] = mom(1, 36, crsp_mom) |  |  |  |
| 26 | Sales growth | 1994 | 1990 | 0.0004 | 0.058 | Lakonishok, Shleifer, and Vishny (1994) | sgr | data_rawq['sgr'] = (data_rawq['saleq4']/data_rawq['saleq4_l4'])-1 | done |  |  |
| 27 | Cash ﬂow-to-price | 1994 | 1990 | 0.0031 | 0.325 | Lakonishok, Shleifer, and Vishny (1994) | cp | data_rawa['cp'] = data_rawa['cf'] / data_rawa['me'] | done | CF | CF |
| 28 | New equity issue | 1995 | 1990 | 0.001 | 0.087 | Loughran and Ritter (1995) | IPO | if count<=12 then IPO=1; else IPO=0; |  |  |  |
| 29 | Dividend initiation | 1995 | 1988 | −0.03% | −3.4% | Michaely, Thaler, and Womack (1995) | divi | if (not missing(dvt) and dvt>0) and (lag(dvt)=0 or missing(lag(dvt))) then divi=1; else divi=0; |  | DivInit | DivInit |
| 30 | Dividend omission | 1995 | 1988 | −0.18% | −18.0% | Michaely, Thaler, and Womack (1995) | divo | if (missing(dvt) or dvt=0) and (lag(dvt)>0 and not missing(lag(dvt))) then divo=1; else divo=0; |  | DivOmit | DivOmit |
| 31 | Working capital accruals | 1996 | 1991 | 0.0022 | 0.46 | Sloan (1996) | acc | (ib-oancf) / ((at+lag(at))/2) | Done | Accruals | Accruals |
| 32 | Sales to price | 1996 | 1991 | 0.0035 | 0.418 | Barbee Jr, Mukherji, and Raines (1996) | sp | data_rawq['sp'] = data_rawq['saleq4']/data_rawq['me'] | done | SP | SP |
| 33 | Capital turnover | 1996 | 1993 | −0.11% | −16.6% | Haugen and Baker (1996) | cto | data_rawa['cto'] = data_rawa['sale'] / data_rawa['at'].shift(1) | done |  |  |
| 34 | Momentum | 1997 | 1993 | 0.0063 | 0.502 | Carhart (1997) | UMD | Publicly sourced replicated | Done |  |  |
| 35 | Share turnover | 1998 | 1991 | −0.02% | −2.1% | Datar, Naik, and Radcliffe (1998) | turn |  | done |  |  |
| 36 | % change in gross margin—% change in sales | 1998 | 1988 | −0.05% | −12.4% | Abarbanell and Bushee (1998) | pchgm_pchsale | (((sale-cogs)-(lag(sale)-lag(cogs)))/(lag(sale)-lag(cogs)))-((sale-lag(sale))/lag(sale)) | Done |  |  |
| 37 | % change in sales—% change in inventory | 1998 | 1988 | 0.0014 | 0.421 | Abarbanell and Bushee (1998) | pchsale_pchinvt | ((sale-lag(sale))/lag(sale))-((invt-lag(invt))/lag(invt)) |  | GrSaleToGrInv | GrSaleToGrInv |
| 38 | % change in sales—% change in A/R | 1998 | 1988 | 0.0014 | 0.435 | Abarbanell and Bushee (1998) | pchsale_pchrect | ((sale-lag(sale))/lag(sale))-((rect-lag(rect))/lag(rect)) |  |  |  |
| 39 | % change in sales—% change in SG&A | 1998 | 1988 | 0.0009 | 0.196 | Abarbanell and Bushee (1998) | pchsale_pchxsga | ( (sale-lag(sale))/lag(sale) )-( (xsga-lag(xsga)) /lag(xsga) ) |  |  |  |
| 40 | Effective Tax Rate | 1998 | 1988 | −0.04% | −9.1% | Abarbanell and Bushee (1998) | etr | data_rawa['etr'] = (data_rawa['txtpi'] - (data_rawa['txtpi_l1'] + data_rawa['txtpi_l2'] + data_rawa['txtpi_l3'])/3) * data_rawa['deps'] |  |  |  |
| 41 | Labor Force Efﬁciency | 1998 | 1988 | −0.03% | −8.5% | Abarbanell and Bushee (1998) | lfe | (sale/emp - l12(sale/emp)) / l12(sale/emp) |  |  |  |
| 42 | Ohlson’s O-score | 1998 | 1995 | 0.0005 | 0.093 | Dichev (1998) | os | OScore = -1.32 - 0.407*ln(at/gnpdefl) + 6.03*(lt/at) - 1.43*((act - lct)/at) + 0.076*(lct/act) - 1.72*I(lt>at) - 2.37*(ib/at) - 1.83*(fopt/lt) + 0.285*I(ib + ib_lag12 < 0) - 0.521*((ib - ib_lag12)/(abs(ib)+abs(ib_lag12))); signal = 1 if OScore is in decile 10, 0 if in deciles 1–7 |  | OScore | OScore |
| 43 | Altman’s Z-score | 1998 | 1995 | 0.002 | 0.221 | Dichev (1998) | zs | 1.2*(act - lct)/at + 1.4*(re/at) + 3.3*(ni + xint + txt)/at + 0.6*(mve_permco/lt) + revt/at |  |  |  |
| 44 | Industry adjusted % change in capital expenditures | 1998 | 1988 | 0.001 | 0.205 | Abarbanell and Bushee (1998) | pchcapx_ia | pchcapx-mean(pchcapx) |  | ChInvIA | ChInvIA |
| 45 | Number of earnings increases | 1999 | 1992 | 0.0001 | 0.028 | Barth, Elliott, and Finn (1999) | nincr | data_rawq['nincr'] = (data_rawq['nincr_temp1'] + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']*data_rawq['nincr_temp6']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']*data_rawq['nincr_temp6']*data_rawq['nincr_temp7']) + (data_rawq['nincr]()]()_*_]()_*_]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()]()_*_]()_*_]()]()_*_]()]() |  |  |  |
| 46 | Industry momentum | 1999 | 1995 | 0.0001 | 0.014 | Moskowitz and Grinblatt (1999) | indmom | df['indmom'] = ((df['Mom6m'] * df['mve_c']).sum()) / df['mve_c'].sum() |  | IndMom | IndMom |
| 47 | Financial statements score | 2000 | 1996 | 0.0008 | 0.184 | Piotroski (2000) | ps | (ni>0)+(oancf>0)+(ni/at > lag(ni)/lag(at))+(oancf>ni)+(dltt/at < lag(dltt)/lag(at))+(act/lct > lag(act)/lag(lct)) +((sale-cogs)/sale > (lag(sale)-lag(cogs))/lag(sale))+ (sale/at > lag(sale)/lag(at))+ (scstkc=0) |  | PS | PS |
| 48 | Industry-adjusted book to market | 2000 | 1998 | 0.0022 | 0.38 | Asness, Porter, and Stevens (2000) | bm_ia | data_rawa['bm_ia'] = data_rawa['bm']/data_rawa['bm_ind'] | done |  |  |
| 49 | Industry-adjusted cash ﬂow to price ratio | 2000 | 1998 | 0.0026 | 0.521 | Asness, Porter, and Stevens (2000) | cfp_ia | cfp-mean(cfp) | In Progress |  |  |
| 50 | Industry-adjusted change in employees | 2000 | 1998 | −0.01% | −1.5% | Asness, Porter, and Stevens (2000) | chempia | hire-mean(hire) | In Progress |  |  |
| 51 | Industry-adjusted size | 2000 | 1998 | 0.0036 | 0.363 | Asness, Porter, and Stevens (2000) | mve_ia | log(me) - median(log(me)) in same Fama-French 49 industry | In Progress |  |  |
| 52 | Dollar trading volume | 2001 | 1995 | 0.0038 | 0.358 | Chordia, Subrahmanyam, and Anshuman (2001) | dolvol | crsp_mom['dolvol'] = np.log(crsp_mom['vol_l2']*crsp_mom['prc_l2']).replace([np.inf, -np.inf], np.nan) | In Progress |  |  |
| 53 | Volatility of liquidity (dollar trading volume) | 2001 | 1995 | 0.002 | 0.388 | Chordia, Subrahmanyam, and Anshuman (2001) | std_dolvol |  | In Progress | VolSD | VolSD |
| 54 | Volatility of liquidity (share turnover) | 2001 | 1995 | 0.0002 | 0.021 | Chordia, Subrahmanyam, and Anshuman (2001) (Continued) 1362 The Journal of Finance R ⃝ | std_turn |  | Done | std_turn | std_turn |
| 55 | Advertising Expense-to-market | 2001 | 1995 | −0.13% | −15.6% | Chan, Lakonishok, and Sougiannis (2001) | adm | data_rawa['adm'] = data_rawa['xad']/data_rawa['me'] | Done | AdExp | AdExp |
| 56 | R&D Expense-to-market | 2001 | 1995 | 0.0034 | 0.362 | Chan, Lakonishok, and Sougiannis (2001) | rdm | data_rawq['rdm'] = data_rawq['xrdq4']/data_rawq['me'] | Done | RD | RD |
| 57 | R&D-to-sales | 2001 | 1995 | 0.0006 | 0.055 | Chan, Lakonishok, and Sougiannis (2001) | rds | data_rawq['xrdq4']/data_rawq['saleq'] | In Progress |  |  |
| 58 | Kaplan-Zingales Index | 2001 | 1997 | 0.0022 | 0.253 | Lamont, Polk, and Saa´a-Requejo (2001) | kz | df['KZ'] = (-1.002 * (ib + dp) / ppent) + (0.283 * (at + mve_permco - ceq - txdb) / at) + (3.139 * (dlc + dltt) / (dlc + dltt + seq))- (39.368 * ((dvc + dvp) / ppent))- (1.315 * (che / ppent)) |  |  |  |
| 59 | Change in inventory | 2002 | 1997 | 0.0018 | 0.407 | Thomas and Zhang (2002) | chinv | (invt-lag(invt))/((at+lag(at))/2) | Done | ChInv | ChInv |
| 60 | Change in tax expense | 2002 | 1997 | 0.0009 | 0.18 | Thomas and Zhang (2002) | chtx | data_rawq['chtx'] = (data_rawq['txtq']-data_rawq['txtq_l4'])/data_rawq['atq_l4'] | In Progress |  |  |
| 61 | Illiquidity | 2002 | 1997 | 0.0034 | 0.286 | Amihud (2002) | ill |  |  | Illiquidity | Illiquidity |
| 62 | Liquidity | 2003 | 2000 | 0.0038 | 0.386 | P´astor and Stambaugh (2003) | LIQ_PS | Publicly sourced replicated | Done | BetaLiquidityPS | BetaLiquidityPS |
| 63 | Idiosyncratic return volatility | 2003 | 1997 | 0.0007 | 0.051 | Ali, Hwang, and Trombley (2003) | idiovol | Standard deviation of returns |  |  |  |
| 64 | Growth in long term net operating assets | 2003 | 1993 | 0.0022 | 0.518 | Fairﬁeld, Whisenant, and Yohn (2003) | grltnoa | data_rawq['grltnoa'] = ((data_rawq['rectq']+data_rawq['invtq']+data_rawq['ppentq']+data_rawq['acoq']+data_rawq['intanq']+data_rawq['aoq']-data_rawq['apq']-data_rawq['lcoq']-data_rawq['loq'])-(data_rawq['rectq_l4']+data_rawq['invtq_l4']+data_rawq['ppentq_l4']+data_rawq['acoq_l4']-data_rawq['apq_l4']-data_rawq['lcoq_l4']-data_rawq['loq_l4'])-(data_rawq['rectq']-data_rawq['rectq_l4']+data_rawq['invtq']-data_rawq['invtq_l4']+data_rawq['acoq']-(data_rawq['apq']-data_rawq['apq_l4']+data_rawq['lcoq']-data_rawq['lcoq_l4'])-ttm4('dpq', data_rawq)))/((data_rawq['atq']+data_rawq['atq_l4'])/2) |  | GrLTNOA | GrLTNOA |
| 65 | Order backlog | 2003 | 1999 | 0.0005 | 0.057 | Rajgopal, Shevlin, and Venkatachalam (2003) | ob_a |  |  | OrderBacklog | OrderBacklog |
| 66 | Changes in Long-term Net Operating Assets | 2003 | 1993 | 0.0024 | 0.56 | Fairﬁeld, Whisenant, and Yohn (2003) | grltnoa_hxz | Δ(noa_longterm) / noa_longterm_lag |  |  |  |
| 67 | Cash ﬂow to price ratio | 2004 | 1997 | 0.0027 | 0.317 | Desai, Rajgopal, and Venkatachalam (2004) | cfp | (ib-( (act-lag(act) - (che-lag(che))) - ( (lct-lag(lct))-(dlc-lag(dlc))-(txp-lag(txp))-dp ) ))/mve_f |  | cfp | cfp |
| 68 | R&D increase | 2004 | 2001 | 0.0006 | 0.111 | Eberhart, Maxwell, and Siddique (2004) | rd | np.where(((data_rawq['xrdq4']/data_rawq['atq'])-data_rawq['xrdq4/atq_l4_l4'])/data_rawq['xrdq4/atq_l4_l4']>0.05, 1, 0) |  | SurpriseRD | SurpriseRD |
| 69 | Corporate investment | 2004 | 1995 | 0.0013 | 0.364 | Titman, Wei, and Xie (2004) | cinvest | * data_rawq['cinvest'] = ((data_rawq['ppentq'] - data_rawq['ppentq_l1']) / data_rawq['saleq'])-(data_rawq[['c_temp1', 'c_temp2', 'c_temp3']].mean(axis=1)) |  | Investment | Investment |
| 70 | Earnings volatility | 2004 | 2001 | 0.001 | 0.107 | Francis et al. (2004) | roavol | std(roaq,lag(roaq),lag2(roaq),lag3(roaq),lag4(roaq),lag5(roaq),lag6(roaq),lag7(roaq), lag8(roaq),lag9(roaq),lag10(roaq),lag11(roaq),lag12(roaq),lag13(roaq),lag14(roaq),lag15(roaq)) |  |  |  |
| 71 | Abnormal Corporate Investment | 2004 | 1995 | 0.0013 | 0.312 | Titman, Wei, and Xie (2004) | cinvest_a | (capx - lag(capx)) / lag(capx) |  |  |  |
| 72 | Net Operating Assets | 2004 | 2002 | 0.0031 | 0.666 | Hirshleifer et al. (2004) | noa | ((data_rawa['at']-data_rawa['che']-data_rawa['ivao'].fillna(0))-(data_rawa['at']-data_rawa['dlc'].fillna(0)-data_rawa['dltt'].fillna(0)-data_rawa['mib'].fillna(0)-data_rawa['pstk'].fillna(0)-data_rawa['ceq'])/data_rawa['at_l1']) |  | NOA | NOA |
| 73 | Changes in Net Operating Assets | 2004 | 2002 | 0.0014 | 0.416 | Hirshleifer et al. (2004) | dnoa | (data_rawa['net_op']-data_rawa['net_op'].shift(1))/ data_rawa['at'].shift(1) |  | dNoa | dNoa |
| 74 | Tax income to book income | 2004 | 2000 | 0.0014 | 0.283 | Lev and Nissim (2004) | tb | rf_lag12 |  | Tax | Tax |
| 75 | Price delay | 2005 | 2001 | 0.0007 | 0.168 | Hou and Moskowitz (2005) | pricedelay |  |  | ZZ2_PriceDelaySlope_PriceDelayRsq_PriceDelayTstat | PriceDelaySlope |
| 76 | # Years since ﬁrst Compustat coverage | 2005 | 2001 | 0.0001 | 0.011 | Jiang, Lee, and Zhang (2005) | age | count |  |  |  |
| 77 | Growth in common shareholder equity | 2005 | 2001 | 0.0015 | 0.276 | Richardson et al. (2005) | egr | ( (ceq-lag(ceq))/lag(ceq) ) |  |  |  |
| 78 | Growth in long-term debt | 2005 | 2001 | 0.0006 | 0.133 | Richardson et al. (2005) | lgr | data_rawq['lgr'] = (data_rawq['ltq']/data_rawq['ltq_l4'])-1 | done |  |  |
| 79 | Change in Current Operating Assets | 2005 | 2001 | 0.0019 | 0.346 | Richardson et al. (2005) | dcoa | data_rawa['dcoa'] = (data_rawa['coa']-data_rawa['coa'].shift(1)) / data_rawa['at'].shift(1) |  | DelCOA | DelCOA |
| 80 | Change in Current Operating Liabilities | 2005 | 2001 | 0.0003 | 0.063 | Richardson et al. (2005) | dcol | ((lct - dlc) - (lag_lct - lag_dlc)) / (0.5 * (at + lag_at)) |  | DelCOL | DelCOL |
| 81 | Changes in Net Noncash Working Capital | 2005 | 2001 | 0.0011 | 0.252 | Richardson et al. (2005) | dwc | data_rawa['dwc'] = (data_rawa['act'] - data_rawa['che']) - (data_rawa['lct'] - data_rawa['dlc']) |  |  |  |
| 82 | Change in Noncurrent Operating Assets | 2005 | 2001 | 0.0021 | 0.445 | Richardson et al. (2005) | dnca | data_rawa['dnca'] = data_rawa['nco'] - data_rawa['nco'].shift(1) |  |  |  |
| 83 | Change in Noncurrent Operating Liabilities | 2005 | 2001 | 0.0004 | 0.096 | Richardson et al. (2005) | dncl |  |  |  |  |
| 84 | Change in Net Noncurrent Operating Assets | 2005 | 2001 | 0.0023 | 0.354 | Richardson et al. (2005) (Continued) Taming the Factor Zoo 1363 | dnco | data_rawa['dnco'] = data_rawa['nco'] - data_rawa['nco'].shift(1) |  |  |  |
| 85 | Change in Net Financial Assets | 2005 | 2001 | 0.0023 | 0.59 | Richardson et al. (2005) | dfin | data_rawa['dfin'] = data_rawa['dfin'] / data_rawa['at'].shift(1) |  | DelNetFin | DelNetFin |
| 86 | Total accruals | 2005 | 2001 | 0.0019 | 0.448 | Richardson et al. (2005) | ta | data_rawa['ta'] = data_rawa['dwc'] + data_rawa['dnco'] + data_rawa['dfin'] |  | TotalAccruals | TotalAccruals |
| 87 | Change in Short-term Investments | 2005 | 2001 | −0.03% | −8.3% | Richardson et al. (2005) | dsti |  |  |  |  |
| 88 | Change in Financial Liabilities | 2005 | 2001 | 0.0018 | 0.561 | Richardson et al. (2005) | dfnl | data_rawa['dfnl'] = data_rawa['dfnl'] / data_rawa['at'].shift(1) |  |  |  |
| 89 | Change in Book Equity | 2005 | 2001 | 0.0017 | 0.3 | Richardson et al. (2005) | egr_hxz |  |  |  |  |
| 90 | Financial statements performance | 2005 | 2001 | 0.0017 | 0.371 | Mohanram (2005) | ms | m1+m2+m3+m4+m5+m6+m7+m8 |  | MS | MS |
| 91 | Change in 6-month momentum | 2006 | 2006 | 0.0021 | 0.298 | Gettleman and Marks (2006) | chmom | ( (1+lag(ret))*(1+lag2(ret))*(1+lag3(ret))*(1+lag4(ret))*(1+lag5(ret))*(1+lag6(ret)) ) - 1 - (( (1+lag7(ret))*(1+lag8(ret))*(1+lag9(ret))*(1+lag10(ret))*(1+lag11(ret))*(1+lag12(ret)) ) - 1) |  |  |  |
| 92 | Growth in capital expenditures | 2006 | 1999 | 0.0014 | 0.304 | Anderson and Garcia-Feijoo (2006) | grcapx | (capx-lag2(capx))/lag2(capx) |  | ZZ1_grcapx_grcapx1y_grcapx3y | grcapx |
| 93 | Return volatility | 2006 | 2000 | −0.02% | −1.7% | Ang et al. (2006) | retvol |  |  | CoskewACX | CoskewACX |
| 94 | Zero trading days | 2006 | 2003 | −0.05% | −4.4% | Liu (2006) | zerotrade |  |  | ZZ1_zerotrade_zerotradeAlt1_zerotradeAlt12 | zerotrade |
| 95 | Three-year Investment Growth | 2006 | 1999 | 0.0011 | 0.236 | Anderson and Garcia-Feijoo (2006) | pchcapx3 | (data_rawa['capx']-data_rawa['capx_l1'])/data_rawa['capx_l1'] |  |  |  |
| 96 | Composite Equity Issuance | 2006 | 2003 | −0.01% | −2.2% | Daniel and Titman (2006) | cei | data_rawa['lg_me'] - data_rawa['lg_ret'] |  | CompEqulss | CompEqulss |
| 97 | Net equity ﬁnance | 2006 | 2000 | 0.0008 | 0.097 | Bradshaw, Richardson, and Sloan (2006) | nef | (sstk - prstkc - dv) / (0.5 * (at + l12_at)) |  | NetEquityFinance | NetEquityFinance |
| 98 | Net debt ﬁnance | 2006 | 2000 | 0.0017 | 0.483 | Bradshaw, Richardson, and Sloan (2006) | ndf | data_rawa['ndf'] = data_rawa['dltis'] - data_rawa['dltr'] + data_rawa['dlcch'] |  | NetDebtFinance | NetDebtFinance |
| 99 | Net external ﬁnance | 2006 | 2000 | 0.0022 | 0.386 | Bradshaw, Richardson, and Sloan (2006) | nxf |  |  | XFIN | XFIN |
| 100 | Revenue Surprises | 2006 | 2003 | 0.0005 | 0.09 | Jegadeesh and Livnat (2006) | rs | (sale - cogs)/at |  | RevenueSurprice | RevenueSurprice |
| 101 | Industry Concentration | 2006 | 2001 | 0.0003 | 0.038 | Hou and Robinson (2006) | herf | data_rawa['herf'] = (data_rawa['sale']/data_rawa['indsale'])*(data_rawa['sale']/data_rawa['indsale']) |  | Herf | Herf |
| 102 | Whited-Wu Index | 2006 | 2001 | −0.02% | −2.6% | Whited and Wu (2006) | ww | WW = -0.091 * ( (ib + dp) / (4*at) ) - 0.062 * I[dvpsx_c > 0] + 0.021 * (dltt / at) - 0.044 * log(at) + 0.102 * ( (tempIndSales / l12_tempIndSales - 1) / 4 ) - 0.035 * ( (sale / l1_sale - 1) / 4 ) |  |  |  |
| 103 | Return on invested capital | 2007 | 2005 | 0.0018 | 0.293 | Brown and Rowe (2007) | roic | (ebit-nopi)/(ceq+lt-che) |  |  |  |
| 104 | Debt capacity/ﬁrm tangibility | 2007 | 2000 | 0.0005 | 0.071 | Almeida and Campello (2007) | tang | (che+rect*0.715+invt*0.547+ppent*0.535)/at |  |  |  |
| 105 | Payout yield | 2007 | 2003 | 0.0016 | 0.175 | Boudoukh et al. (2007) | op | (ttm4('revtq', data_rawq)-ttm4('cogsq', data_rawq)-ttm4('xsgaq0', data_rawq)-ttm4('xintq0', data_rawq))/data_rawq['beq_l4'] |  | PayoutYield | PayoutYield |
| 106 | Net payout yield | 2007 | 2003 | 0.0016 | 0.172 | Boudoukh et al. (2007) | nop | data_rawa['nop'] = np.where(data_rawa['nop']<=0, np.nan, data_rawa['nop'] ) |  | NetPayoutYield | NetPayoutYield |
| 107 | Net debt-to-price | 2007 | 1950 | 0.0002 | 0.025 | Penman, Richardson, and Tuna (2007) | ndp | ((dltt + dlc + pstk + dvpa - tstkp) - che) / mve_permco |  | NetDebtPrice | NetDebtPrice |
| 108 | Enterprise book-to-price | 2007 | 2001 | 0.0014 | 0.147 | Penman, Richardson, and Tuna (2007) | ebp | data_rawa['ebp'] = (data_rawa['n_debt']+data_rawa['ber']) / (data_rawa['n_debt']+data_rawa['me']) |  | ZZ1_EBM_BPEBM | EBM |
| 109 | Change in shares outstanding | 2008 | 1969 | 0.0024 | 0.361 | Pontiff and Woodgate (2008) | chcsho | data_rawq['chcsho'] = (data_rawq['cshoq']/data_rawq['cshoq_l4'])-1 |  | Sharelss1Y | Sharelss1Y |
| 110 | Abnormal earnings announcement volume | 2008 | 2006 | −0.08% | −17.0% | Lerman, Livnat, and Mendenhall (2008) | aeavol |  |  |  |  |
| 111 | Earnings announcement return | 2008 | 2004 | 0.0002 | 0.068 | Brandt et al. (2008) | ear |  |  | ZZ2_AnnouncementReturn | AnnouncementReturn |
| 112 | Seasonality | 2008 | 2002 | 0.0016 | 0.173 | Heston and Sadka (2008) | moms12m | mom(1, 12) |  | Mom12mOffSeason | Mom12mOffSeason |
| 113 | Changes in PPE and Inventory-to-assets | 2008 | 2005 | 0.0019 | 0.42 | Lyandres, Sun, and Zhang (2008) | dpia | data_rawa['dpia'] = (data_rawa['c_propty'] + data_rawa['c_invt']) / data_rawa['at'].shift(1) |  | InvestPPEInv | InvestPPEInv |
| 114 | Investment Growth | 2008 | 2003 | 0.0017 | 0.395 | Xing (2008) | pchcapx | (capx-lag(capx))/lag(capx) |  |  |  |
| 115 | Composite Debt Issuance | 2008 | 2005 | 0.0008 | 0.216 | Lyandres, Sun, and Zhang (2008) (Continued) 1364 The Journal of Finance R ⃝ | cdi | LN((dltt + dlc) / l60_tempBD) |  | CompositeDebtIssuance | CompositeDebtIssuance |
| 116 | Return on net operating assets | 2008 | 2002 | 0.0009 | 0.086 | Soliman (2008) | rna | data_rawa['oiadp']/data_rawa['noa_l1'] |  | ChNNCOA | ChNNCOA |
| 117 | Proﬁt margin | 2008 | 2002 | 0.0002 | 0.044 | Soliman (2008) | pm |  | done |  |  |
| 118 | Asset turnover | 2008 | 2002 | 0.0006 | 0.067 | Soliman (2008) | ato | data_rawq['ato'] = data_rawq['saleq']/data_rawq['noa_l4'] |  |  |  |
| 119 | Industry-adjusted change in asset turnover | 2008 | 2002 | 0.0014 | 0.411 | Soliman (2008) | chatoia | (sale / (0.5 * ((rect + invt + aco + ppent + intan - ap - lco - lo) + temp_l12))) - AssetTurnover_l12 |  | ChAssetTurnover | ChAssetTurnover |
| 120 | Industry-adjusted change in proﬁt margin | 2008 | 2002 | −0.01% | −3.2% | Soliman (2008) | chpmia | (pm - lag(pm)) - median(pm - lag(pm)) in same Fama-French 49 industry |  |  |  |
| 121 | Cash productivity | 2009 | 2009 | 0.0027 | 0.376 | Chandrashekar and Rao (2009) | cashpr | ((mve_f+dltt-at)/che) | done | CashProd | CashProd |
| 122 | Sin stocks | 2009 | 2006 | 0.0044 | 0.416 | Hong and Kacperczyk (2009) | sin |  |  | sinAlgo | sinAlgo |
| 123 | Revenue surprise | 2009 | 2005 | 0.0012 | 0.193 | Kama (2009) | rsup | data_rawq['rsup'] = (data_rawq['saleq'] - data_rawq['saleq_l4'])/data_rawq['me'] |  |  |  |
| 124 | Cash ﬂow volatility | 2009 | 2008 | 0.002 | 0.266 | Huang (2009) | stdcf | std(scf,lag(scf),lag2(scf),lag3(scf),lag4(scf),lag5(scf),lag6(scf),lag7(scf), lag8(scf),lag9(scf),lag10(scf),lag11(scf),lag12(scf),lag13(scf),lag14(scf),lag15(scf)) |  |  |  |
| 125 | Absolute accruals | 2010 | 2008 | −0.05% | −8.6% | Bandyopadhyay, Huang, and Wirjanto (2010) | absacc | abs(acc) |  |  |  |
| 126 | Capital expenditures and inventory | 2010 | 2006 | 0.0019 | 0.428 | Chen and Zhang (2010) | invest | ( (ppegt-lag(ppegt)) + (invt-lag(invt)) ) / lag(at) |  |  |  |
| 127 | Return on assets | 2010 | 2005 | −0.09% | −13.9% | Balakrishnan, Bartov, and Faurel (2010) | roaq | ibq/lag(atq) | done | roaq | roaq |
| 128 | Accrual volatility | 2010 | 2008 | 0.0019 | 0.266 | Bandyopadhyay, Huang, and Wirjanto (2010) | stdacc | std(sacc,lag(sacc),lag2(sacc),lag3(sacc),lag4(sacc),lag5(sacc),lag6(sacc),lag7(sacc), lag8(sacc),lag9(sacc),lag10(sacc),lag11(sacc),lag12(sacc),lag13(sacc),lag14(sacc),lag15(sacc)) |  |  |  |
| 129 | Industry-adjusted Real Estate Ratio | 2010 | 2005 | 0.0011 | 0.173 | Tuzel (2010) | realestate_hxz | IFERROR((fatb + fatl) / ppegt, (ppenb + ppenls) / ppent) - tempMean |  | realestate | realestate |
| 130 | Percent accruals | 2011 | 2008 | 0.0016 | 0.35 | Hafzalla et al. (2011) | pctacc | (ib-oancf)/abs(ib) | done | PctAcc | PctAcc |
| 131 | Maximum daily return | 2011 | 2005 | 0 | −0.3% | Bali, Cakici, and Whitelaw (2011) | maxret |  |  | MaxRet | MaxRet |
| 132 | Operating Leverage | 2011 | 2008 | 0.002 | 0.328 | Novy-Marx (2011) | ol | data_rawa['ol'] = (data_rawa['cogs'] + data_rawa['xsga'])/data_rawa['at'] |  | OPLeverage | OPLeverage |
| 133 | Inventory Growth | 2011 | 2009 | 0.0013 | 0.301 | Belo and Lin (2011) | ivg |  |  | InvGrowth | InvGrowth |
| 134 | Percent Operating Accruals | 2011 | 2008 | 0.0015 | 0.289 | Hafzalla et al. (2011) | poa | data_rawa['poa'] = data_rawa['oa']/data_rawa['ni'] |  |  |  |
| 135 | Enterprise multiple | 2011 | 2009 | 0.0011 | 0.176 | Loughran and Wellman (2011) | em | data_rawa['em'] = data_rawa['enteprs_v'] / data_rawa['oibdp'] |  | EntMult | EntMult |
| 136 | Cash holdings | 2012 | 2009 | 0.0013 | 0.153 | Palazzo (2012) | cash | data_rawq['cash'] = data_rawq['cheq']/data_rawq['atq'] | Done | Cash | Cash |
| 137 | HML Devil | 2013 | 2011 | 0.0023 | 0.226 | Asness and Frazzini (2013) | HML_Devil | Publicly sourced replicated | Done |  |  |
| 138 | Gross proﬁtability | 2013 | 2010 | 0.0015 | 0.225 | Novy-Marx (2013) | gma | data_rawq['gma'] = (data_rawq['revtq4']-data_rawq['cogsq4'])/data_rawq['atq_l4'] | done | GP | GP |
| 139 | Organizational Capital | 2013 | 2008 | 0.0021 | 0.319 | Eisfeldt and Papanikolaou (2013) | orgcap | orgcap_1/avgat |  | ZZ1_OrgCap_OrgCapNoAdj | OrgCap |
| 140 | Betting Against Beta | 2014 | 2012 | 0.0091 | 0.928 | Frazzini and Pedersen (2014) | BAB | Publicly sourced replicated | Done | ZZ2_BetaFP | BetaFP |
| 141 | Quality Minus Junk | 2014 | 2012 | 0.0043 | 0.601 | Asness, Frazzini, and Pedersen (2019) | QMJ | Publicly sourced replicated | Done |  |  |
| 142 | Employee growth rate | 2014 | 2010 | 0.0008 | 0.129 | Belo, Lin, and Bazdresch (2014) | hire | data_rawa['hire'] = (data_rawa['emp'] - data_rawa['emp_l1'])/data_rawa['emp_l1'] | in progress | hire | hire |
| 143 | Growth in advertising expense | 2014 | 2010 | 0.0007 | 0.13 | Lou (2014) | gad |  |  | GrAdExp | GrAdExp |
| 144 | Book Asset Liquidity | 2014 | 2006 | 0.0009 | 0.123 | Ortiz-Molina and Phillips (2014) | ala | data_rawq['ala'] = data_rawq['cheq'] + 0.75*(data_rawq['actq']-data_rawq['cheq'])+0.5*(data_rawq['atq']-data_rawq['actq']-data_rawq['gdwlq']-data_rawq['intanq']) |  |  |  |
| 145 | Robust Minus Weak | 2015 | 2013 | 0.0034 | 0.498 | Fama and French (2015) | RMW | Publicly sourced replicated | Done |  |  |
| 146 | Conservative Minus Aggressive | 2015 | 2013 | 0.0026 | 0.468 | Fama and French (2015) | CMA | Publicly sourced replicated | Done |  |  |
| 147 | HXZ Investment | 2015 | 2012 | 0.0034 | 0.647 | Hou, Xue, and Zhang (2015) | HXZ_IA | Publicly sourced replicated | Done |  |  |
| 148 | HXZ Proﬁtability | 2015 | 2012 | 0.0057 | 0.775 | Hou, Xue, and Zhang (2015) | HXZ_ROE | Publicly sourced replicated | Done |  |  |
| 149 | Intermediary Investment | 2016 | 2012 |  |  | He, Kelly, and Manela (2017) | Intermediary | Publicly sourced replicated | Done |  |  |
| 150 | Convertible debt indicator | 2016 | 2012 | 0.0011 | 0.264 | Valta (2016) | convind |  | done | ConvDebt | ConvDebt |