### coverage

| factor | acronym match | inferred acronym | covered | Name | factor_definition | source | csv row | SAS row |
| :------ | :------------- | :---------------- | :------- | :---- | :----------------- | :------ | :------- | :------- |
| beta | exact |  | PARTIAL | Beta rolling 3m |  | Repo | 87.0 |  |
| ep | exact |  | True | Earnings-to-price | data_rawq['ep'] = data_rawq['ibq4']/data_rawq['me'] | Repo | 20.0 |  |
| dy | exact |  | True | Dividend yield | dvt/mve_f | SAS |  | 125.0 |
| sue | exact |  | PARTIAL | Unexpected quarterly earnings |  | Repo | 123.0 |  |
| pps | exact |  | True | Lagged price (log) | 1/prc | SAS |  | 518.0 |
| lev | exact |  | True | Leverage | data_rawq['lev'] = data_rawq['ltq']/data_rawq['me'] | Repo | 102.0 |  |
| cashdebt | exact |  | True | Cash ﬂow to debt | data_rawq['cashdebt'] = (ttm4('ibq', data_rawq) + ttm4('dpq', data_rawq))/((data_rawq['ltq']+data_rawq['ltq_l4'])/2) | Repo | 90.0 |  |
| currat | exact |  | True | Current ratio | act/lct | SAS |  | 178.0 |
| pchcurrat | exact |  | True | Change in current ratio | ((act/lct)-(lag(act)/lag(lct)))/(lag(act)/lag(lct)) | SAS |  | 179.0 |
| pchquick | exact |  | True | Change in quick ratio | ( (act-invt)/lct - (lag(act)-lag(invt))/lag(lct) )/ ( ( lag(act)-lag(invt) )/lag(lct) ) | SAS |  | 181.0 |
| pchsaleinv | exact |  | True | Change in sales-to-inventory ratio | ( (sale/invt)-(lag(sale)/lag(invt)) ) / (lag(sale)/lag(invt)) | SAS |  | 185.0 |
| quick | exact |  | True | Quick ratio | (act-invt)/lct | SAS |  | 180.0 |
| salecash | exact |  | True | Sales-to-cash ratio | sale/che | SAS |  | 182.0 |
| saleinv | exact |  | True | Sales-to-inventory ratio | sale/invt | SAS |  | 184.0 |
| salerec | exact |  | True | Sales-to-receivables ratio | sale/rect | SAS |  | 183.0 |
| baspread | exact |  | PARTIAL | Bid-ask spread rolling 3m |  | Repo | 86.0 |  |
| depr | exact |  | True | Depreciation / PP&E | data_rawq['depr'] = ttm4('dpq', data_rawq)/data_rawq['ppentq'] | Repo | 95.0 |  |
| pchdepr | exact |  | True | Change in depreciation-to-PPE ratio | ((dp/ppent)-(lag(dp)/lag(ppent)))/(lag(dp)/lag(ppent)) | SAS |  | 160.0 |
| mom6m | exact |  | True | Momentum rolling 6m | crsp_mom['mom6m'] = mom(1, 6, crsp_mom) | Repo | 110.0 |  |
| mom36m | exact |  | True | Momentum rolling 36m | crsp_mom['mom36m'] = mom(1, 36, crsp_mom) | Repo | 108.0 |  |
| sgr | exact |  | True | Sales growth | data_rawq['sgr'] = (data_rawq['saleq4']/data_rawq['saleq4_l4'])-1 | Repo | 120.0 |  |
| cp | exact |  | True | Cash ﬂow-to-price | data_rawa['cp'] = data_rawa['cf'] / data_rawa['me'] | Repo | 7.0 |  |
| IPO | exact |  | True | Initial public offering indicator | if count<=12 then IPO=1; else IPO=0; | SAS |  | 987.0 |
| divi | exact |  | True | Dividend initiation indicator | if (not missing(dvt) and dvt>0) and (lag(dvt)=0 or missing(lag(dvt))) then divi=1; else divi=0; | SAS |  | 189.0 |
| divo | exact |  | True | Dividend omission indicator | if (missing(dvt) or dvt=0) and (lag(dvt)>0 and not missing(lag(dvt))) then divo=1; else divo=0; | SAS |  | 190.0 |
| acc | exact |  | True | Accruals ratio | (ib-oancf) / ((at+lag(at))/2) | SAS |  | 135.0 |
| sp | exact |  | True | Sales-to-price | data_rawq['sp'] = data_rawq['saleq4']/data_rawq['me'] | Repo | 14.0 |  |
| cto | exact |  | True | Capital Turnover | data_rawa['cto'] = data_rawa['sale'] / data_rawa['at'].shift(1) | Repo | 60.0 |  |
| turn | exact |  | PARTIAL | Shares turnover |  | Repo | 124.0 |  |
| pchgm_pchsale | exact |  | True | Change in gross margin relative to change in sales | (((sale-cogs)-(lag(sale)-lag(cogs)))/(lag(sale)-lag(cogs)))-((sale-lag(sale))/lag(sale)) | SAS |  | 157.0 |
| pchsale_pchinvt | exact |  | True | Difference between sales growth and inventory growth | ((sale-lag(sale))/lag(sale))-((invt-lag(invt))/lag(invt)) | SAS |  | 155.0 |
| pchsale_pchrect | exact |  | True | Difference between sales growth and receivables growth | ((sale-lag(sale))/lag(sale))-((rect-lag(rect))/lag(rect)) | SAS |  | 156.0 |
| pchsale_pchxsga | exact |  | True | Difference between sales growth and SG&A growth | ( (sale-lag(sale))/lag(sale) )-( (xsga-lag(xsga)) /lag(xsga) ) | SAS |  | 158.0 |
| etr | exact |  | True | Eﬀective Tax Rate | data_rawa['etr'] = (data_rawa['txtpi'] - (data_rawa['txtpi_l1'] + data_rawa['txtpi_l2'] + data_rawa['txtpi_l3'])/3) * data_rawa['deps'] | Repo | 67.0 |  |
| lfe | inferred | LaborforceEfficiency | True | Laborforce efficiency | (sale/emp - l12(sale/emp)) / l12(sale/emp) | OpenSourceAP |  |  |
| os | inferred | OScore | True | O-Score bankruptcy predictor | OScore = -1.32 - 0.407*ln(at/gnpdefl) + 6.03*(lt/at) - 1.43*((act - lct)/at) + 0.076*(lct/act) - 1.72*I(lt>at) - 2.37*(ib/at) - 1.83*(fopt/lt) + 0.285*I(ib + ib_lag12 < 0) - 0.521*((ib - ib_lag12)/(abs(ib)+abs(ib_lag12))); signal = 1 if OScore is in decile 10, 0 if in deciles 1–7 | OpenSourceAP |  |  |
| zs | inferred | ZScore | True | Altman Z-Score | 1.2*(act - lct)/at + 1.4*(re/at) + 3.3*(ni + xint + txt)/at + 0.6*(mve_permco/lt) + revt/at | OpenSourceAP |  |  |
| pchcapx_ia | exact |  | True | Industry-adjusted change in capital expenditures | pchcapx-mean(pchcapx) | SAS |  | 243.0 |
| nincr | exact |  | True | Number of earnings increases | data_rawq['nincr'] = (data_rawq['nincr_temp1'] + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']*data_rawq['nincr_temp6']) + (data_rawq['nincr_temp1']*data_rawq['nincr_temp2']*data_rawq['nincr_temp3']*data_rawq['nincr_temp4']*data_rawq['nincr_temp5']*data_rawq['nincr_temp6']*data_rawq['nincr_temp7']) + (data_rawq['nincr]()]()_*_]()_*_]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()_*_]()]()_*_]()_*_]()_*_]()]()_*_]()_*_]()]()_*_]()]() | Repo | 111.0 |  |
| indmom | exact |  | True | Industry momentum (2-digit SIC, value-weighted; Grinblatt–Moskowitz style) | df['indmom'] = ((df['Mom6m'] * df['mve_c']).sum()) / df['mve_c'].sum() | OpenSourceAP |  |  |
| ps | exact |  | True | Piotroski F-score | (ni>0)+(oancf>0)+(ni/at > lag(ni)/lag(at))+(oancf>ni)+(dltt/at < lag(dltt)/lag(at))+(act/lct > lag(act)/lag(lct)) +((sale-cogs)/sale > (lag(sale)-lag(cogs))/lag(sale))+ (sale/at > lag(sale)/lag(at))+ (scstkc=0) | SAS |  | 204.0 |
| bm_ia | exact |  | True | Industry-adjusted book to market | data_rawa['bm_ia'] = data_rawa['bm']/data_rawa['bm_ind'] | Repo | 88.0 |  |
| cfp_ia | exact |  | True | Industry-adjusted cash flow-to-price ratio | cfp-mean(cfp) | SAS |  | 244.0 |
| chempia | exact |  | True | Industry-adjusted change in employment | hire-mean(hire) | SAS |  | 242.0 |
| mve_ia | inferred | me_ia(mve_ia) | True | Industry-adjusted log of market value of equity | log(me) - median(log(me)) in same Fama-French 49 industry | Repo | 105.0 |  |
| dolvol | exact |  | True | Dollar trading volume | crsp_mom['dolvol'] = np.log(crsp_mom['vol_l2']*crsp_mom['prc_l2']).replace([np.inf, -np.inf], np.nan) | Repo | 96.0 |  |
| std_dolvol | exact |  | PARTIAL | Std of dollar trading volume rolling 3m |  | Repo | 121.0 |  |
| std_turn | exact |  | PARTIAL | Std. of Share turnover rolling 3m |  | Repo | 122.0 |  |
| adm | exact |  | True | Advertising Expense-to-market | data_rawa['adm'] = data_rawa['xad']/data_rawa['me'] | Repo | 66.0 |  |
| rdm | exact |  | True | R&D Expense-to-market | data_rawq['rdm'] = data_rawq['xrdq4']/data_rawq['me'] | Repo | 68.0 |  |
| rds | exact |  | True | Quarterly R&D Expense-to-sales | data_rawq['xrdq4']/data_rawq['saleq'] | Repo_accounting | 72.0 |  |
| kz | exact |  | True | Kaplan–Zingales (KZ) financial constraints index (placebo version) | df['KZ'] = (-1.002 * (ib + dp) / ppent) + (0.283 * (at + mve_permco - ceq - txdb) / at) + (3.139 * (dlc + dltt) / (dlc + dltt + seq))- (39.368 * ((dvc + dvp) / ppent))- (1.315 * (che / ppent)) | OpenSourceAP |  |  |
| chinv | exact |  | True | Change in inventory relative to assets | (invt-lag(invt))/((at+lag(at))/2) | SAS |  | 145.0 |
| chtx | exact |  | True | Change in tax expense | data_rawq['chtx'] = (data_rawq['txtq']-data_rawq['txtq_l4'])/data_rawq['atq_l4'] | Repo | 93.0 |  |
| ill | exact |  | PARTIAL | Illiquidity rolling 3m |  | Repo | 101.0 |  |
| idiovol | inferred | idivol | True | Idiosyncratic volatility | Standard deviation of returns | SAS | 516.0 |  |
| grltnoa | exact |  | True | Growth in long-term net operating assets | data_rawq['grltnoa'] = ((data_rawq['rectq']+data_rawq['invtq']+data_rawq['ppentq']+data_rawq['acoq']+data_rawq['intanq']+data_rawq['aoq']-data_rawq['apq']-data_rawq['lcoq']-data_rawq['loq'])-(data_rawq['rectq_l4']+data_rawq['invtq_l4']+data_rawq['ppentq_l4']+data_rawq['acoq_l4']-data_rawq['apq_l4']-data_rawq['lcoq_l4']-data_rawq['loq_l4'])-(data_rawq['rectq']-data_rawq['rectq_l4']+data_rawq['invtq']-data_rawq['invtq_l4']+data_rawq['acoq']-(data_rawq['apq']-data_rawq['apq_l4']+data_rawq['lcoq']-data_rawq['lcoq_l4'])-ttm4('dpq', data_rawq)))/((data_rawq['atq']+data_rawq['atq_l4'])/2) | Repo | 98.0 |  |
| ob_a | opensource |  | True | Order backlog |  | OpenSourceAP |  |  |
| grltnoa_hxz | inferred | grltnoa | True | Growth in Long-Term Net Operating Assets | Δ(noa_longterm) / noa_longterm_lag | Repo | 98.0 |  |
| cfp | exact |  | True | Cash flow-to-price | (ib-( (act-lag(act) - (che-lag(che))) - ( (lct-lag(lct))-(dlc-lag(dlc))-(txp-lag(txp))-dp ) ))/mve_f | SAS |  | 141.0 |
| rd | exact |  | True | R&D increase indicator | np.where(((data_rawq['xrdq4']/data_rawq['atq'])-data_rawq['xrdq4/atq_l4_l4'])/data_rawq['xrdq4/atq_l4_l4']>0.05, 1, 0) | Repo_accounting |  |  |
| cinvest | exact |  | True | Corporate investment | * data_rawq['cinvest'] = ((data_rawq['ppentq'] - data_rawq['ppentq_l1']) / data_rawq['saleq'])-(data_rawq[['c_temp1', 'c_temp2', 'c_temp3']].mean(axis=1)) | Repo | 94.0 |  |
| roavol | exact |  | True | Return on assets volatility | std(roaq,lag(roaq),lag2(roaq),lag3(roaq),lag4(roaq),lag5(roaq),lag6(roaq),lag7(roaq), lag8(roaq),lag9(roaq),lag10(roaq),lag11(roaq),lag12(roaq),lag13(roaq),lag14(roaq),lag15(roaq)) | SAS |  | 574.0 |
| cinvest_a | inferred | cinvest | True | Corporate Investment Growth | (capx - lag(capx)) / lag(capx) | Repo | 94.0 |  |
| noa | exact |  | True | Net Operating Assets | ((data_rawa['at']-data_rawa['che']-data_rawa['ivao'].fillna(0))-(data_rawa['at']-data_rawa['dlc'].fillna(0)-data_rawa['dltt'].fillna(0)-data_rawa['mib'].fillna(0)-data_rawa['pstk'].fillna(0)-data_rawa['ceq'])/data_rawa['at_l1']) | Repo_accounting | 41.0 |  |
| dnoa | exact |  | True | Changes in Net Operating Assets | (data_rawa['net_op']-data_rawa['net_op'].shift(1))/ data_rawa['at'].shift(1) | Repo_accounting | 41.0 |  |
| tb | inferred | Tbi q 12 | True | Lagged Treasury bill rate (3-month T-bill) | rf_lag12 | Repo | 55.0 |  |
| pricedelay | opensource |  | True | Price delay |  | OpenSourceAP |  |  |
| age | exact |  | True | Firm age | count | SAS |  | 144.0 |
| egr | exact |  | True | Equity growth | ( (ceq-lag(ceq))/lag(ceq) ) | SAS |  | 164.0 |
| lgr | exact |  | True | Growth in long-term debt | data_rawq['lgr'] = (data_rawq['ltq']/data_rawq['ltq_l4'])-1 | Repo | 103.0 |  |
| dcoa | exact |  | True | changes in Current Operating Assets | data_rawa['dcoa'] = (data_rawa['coa']-data_rawa['coa'].shift(1)) / data_rawa['at'].shift(1) | Repo | 28.0 |  |
| dcol | inferred | DelCOL | True | Change in current operating liabilities | ((lct - dlc) - (lag_lct - lag_dlc)) / (0.5 * (at + lag_at)) | OpenSourceAP |  |  |
| dwc | exact |  | True | Net working capital | data_rawa['dwc'] = (data_rawa['act'] - data_rawa['che']) - (data_rawa['lct'] - data_rawa['dlc']) | Repo_accounting |  |  |
| dnca | exact |  | True | changes in Non-current Operating Assets | data_rawa['dnca'] = data_rawa['nco'] - data_rawa['nco'].shift(1) | Repo | 29.0 |  |
| dncl | missing |  | False |  |  |  |  |  |
| dnco | exact |  | True | Changes in Net Non-current Operating Assets | data_rawa['dnco'] = data_rawa['nco'] - data_rawa['nco'].shift(1) | Repo | 30.0 |  |
| dfin | exact |  | True | changes in Financial Liabilities | data_rawa['dfin'] = data_rawa['dfin'] / data_rawa['at'].shift(1) | Repo | 33.0 |  |
| ta | exact |  | True | Total Accruals | data_rawa['ta'] = data_rawa['dwc'] + data_rawa['dnco'] + data_rawa['dfin'] | Repo | 27.0 |  |
| dsti | inferred | DelSTI | True | Change in short-term investment | (ivst - l12_ivst) / (0.5 * (at + l12_at)) | OpenSourceAP |  |  |
| dfnl | exact |  | True | changes in Book Equity | data_rawa['dfnl'] = data_rawa['dfnl'] / data_rawa['at'].shift(1) | Repo | 34.0 |  |
| egr_hxz | missing |  | False |  |  |  |  |  |
| ms | exact |  | True | Mohanram G-score components | m1+m2+m3+m4+m5+m6+m7+m8 | SAS |  | 796.0 |
| chmom | exact |  | True | Change in momentum (6-month minus previous 6-month) | ( (1+lag(ret))*(1+lag2(ret))*(1+lag3(ret))*(1+lag4(ret))*(1+lag5(ret))*(1+lag6(ret)) ) - 1 - (( (1+lag7(ret))*(1+lag8(ret))*(1+lag9(ret))*(1+lag10(ret))*(1+lag11(ret))*(1+lag12(ret)) ) - 1) | SAS |  | 967.0 |
| grcapx | exact |  | True | Change in capital expenditures (2-year) | (capx-lag2(capx))/lag2(capx) | SAS |  | 167.0 |
| retvol | opensource |  | True | Return volatility |  | OpenSourceAP |  |  |
| zerotrade | exact |  | PARTIAL | Number of zero-trading days rolling 3m |  | Repo | 125.0 |  |
| pchcapx3 | exact |  | True | Change in capital expenditures (1-year) | (data_rawa['capx']-data_rawa['capx_l1'])/data_rawa['capx_l1'] | Repo_accounting |  |  |
| cei | exact |  | True | Composite equity issuance | data_rawa['lg_me'] - data_rawa['lg_ret'] | Repo_accounting |  |  |
| nef | inferred | NetEquityFinance | True | Net equity financing | (sstk - prstkc - dv) / (0.5 * (at + l12_at)) | OpenSourceAP |  |  |
| ndf | exact |  | True | Net debt ﬁnance | data_rawa['ndf'] = data_rawa['dltis'] - data_rawa['dltr'] + data_rawa['dlcch'] | Repo | 38.0 |  |
| nxf | opensource |  | True | Net external ﬁnance |  | OpenSourceAP |  |  |
| rs | inferred | rsup | True | Sales-based measure of financing (sales minus cost of goods sold, scaled by total assets) | (sale - cogs)/at | Repo | 116.0 |  |
| herf | exact |  | True | Industry sales concentration | data_rawa['herf'] = (data_rawa['sale']/data_rawa['indsale'])*(data_rawa['sale']/data_rawa['indsale']) | Repo | 99.0 |  |
| ww | exact |  | True | Whited–Wu (WW) financial constraints index (placebo version) | WW = -0.091 * ( (ib + dp) / (4*at) ) - 0.062 * I[dvpsx_c > 0] + 0.021 * (dltt / at) - 0.044 * log(at) + 0.102 * ( (tempIndSales / l12_tempIndSales - 1) / 4 ) - 0.035 * ( (sale / l1_sale - 1) / 4 ) | OpenSourceAP |  |  |
| roic | exact |  | True | Return on invested capital | (ebit-nopi)/(ceq+lt-che) | SAS |  | 128.0 |
| tang | exact |  | True | Asset tangibility | (che+rect*0.715+invt*0.547+ppent*0.535)/at | SAS |  | 173.0 |
| op | exact |  | True | Operating proﬁtability | (ttm4('revtq', data_rawq)-ttm4('cogsq', data_rawq)-ttm4('xsgaq0', data_rawq)-ttm4('xintq0', data_rawq))/data_rawq['beq_l4'] | Repo_accounting | 112.0 |  |
| nop | exact |  | True | Net operating profit (positive only) | data_rawa['nop'] = np.where(data_rawa['nop']<=0, np.nan, data_rawa['nop'] ) | Repo_accounting |  |  |
| ndp | inferred | NetDebtPrice | True | Net debt to price | ((dltt + dlc + pstk + dvpa - tstkp) - che) / mve_permco | OpenSourceAP |  |  |
| ebp | exact |  | True | Enterprise Book-to-price | data_rawa['ebp'] = (data_rawa['n_debt']+data_rawa['ber']) / (data_rawa['n_debt']+data_rawa['me']) | Repo | 18.0 |  |
| chcsho | exact |  | True | Change in shares outstanding | data_rawq['chcsho'] = (data_rawq['cshoq']/data_rawq['cshoq_l4'])-1 | Repo | 91.0 |  |
| aeavol | missing |  | False |  |  |  |  |  |
| ear | opensource |  | True | Earnings announcement return |  | OpenSourceAP |  |  |
| moms12m | inferred | mom12m | True | 12-Month Momentum | mom(1, 12) | Repo | 106.0 |  |
| dpia | exact |  | True | Changes in PPE and Inventory-to-assets | data_rawa['dpia'] = (data_rawa['c_propty'] + data_rawa['c_invt']) / data_rawa['at'].shift(1) | Repo | 40.0 |  |
| pchcapx | exact |  | True | Change in capital expenditures | (capx-lag(capx))/lag(capx) | SAS |  | 166.0 |
| cdi | inferred | CompositeDebtIssuance | True | Composite debt issuance | LN((dltt + dlc) / l60_tempBD) | OpenSourceAP |  |  |
| rna | exact |  | True | Quarterly Return on Net Operating Assets, Quarterly Asset Turnover | data_rawa['oiadp']/data_rawa['noa_l1'] | Repo_accounting | 61.0 |  |
| pm | exact |  | PARTIAL | proﬁt margin |  | Repo | 59.0 |  |
| ato | exact |  | True | Asset Turnover | data_rawq['ato'] = data_rawq['saleq']/data_rawq['noa_l4'] | Repo | 58.0 |  |
| chatoia | inferred | ChAssetTurnover | True | Change in Asset Turnover | (sale / (0.5 * ((rect + invt + aco + ppent + intan - ap - lco - lo) + temp_l12))) - AssetTurnover_l12 | OpenSourceAP |  |  |
| chpmia | inferred | chpm(chpmia) | True | Change in profit margin (industry-adjusted) | (pm - lag(pm)) - median(pm - lag(pm)) in same Fama-French 49 industry | Repo | 92.0 |  |
| cashpr | exact |  | True | Cash-to-price ratio | ((mve_f+dltt-at)/che) | SAS |  | 124.0 |
| sin | opensource |  | True | Sin stocks |  | OpenSource |  |  |
| rsup | exact |  | True | Revenue surprise | data_rawq['rsup'] = (data_rawq['saleq'] - data_rawq['saleq_l4'])/data_rawq['me'] | Repo | 116.0 |  |
| stdcf | exact |  | True | Cash flow volatility | std(scf,lag(scf),lag2(scf),lag3(scf),lag4(scf),lag5(scf),lag6(scf),lag7(scf), lag8(scf),lag9(scf),lag10(scf),lag11(scf),lag12(scf),lag13(scf),lag14(scf),lag15(scf)) | SAS |  | 578.0 |
| absacc | exact |  | True | Absolute value of accruals | abs(acc) | SAS |  | 143.0 |
| invest | exact |  | True | Investment growth | ( (ppegt-lag(ppegt)) + (invt-lag(invt)) ) / lag(at) | SAS |  | 162.0 |
| roaq | exact |  | True | Return on assets (quarterly) | ibq/lag(atq) | SAS |  | 565.0 |
| stdacc | exact |  | True | Accrual volatility | std(sacc,lag(sacc),lag2(sacc),lag3(sacc),lag4(sacc),lag5(sacc),lag6(sacc),lag7(sacc), lag8(sacc),lag9(sacc),lag10(sacc),lag11(sacc),lag12(sacc),lag13(sacc),lag14(sacc),lag15(sacc)) | SAS |  | 570.0 |
| realestate_hxz | inferred | realestate | True | Real estate holdings | IFERROR((fatb + fatl) / ppegt, (ppenb + ppenls) / ppent) - tempMean | OpenSourceAP |  |  |
| pctacc | exact |  | True | Percent accruals | (ib-oancf)/abs(ib) | SAS |  | 137.0 |
| maxret | exact |  | PARTIAL | Maximum daily returns rolling 3m |  | Repo | 104.0 |  |
| ol | exact |  | True | Operating Leverage | data_rawa['ol'] = (data_rawa['cogs'] + data_rawa['xsga'])/data_rawa['at'] | Repo | 73.0 |  |
| ivg | exact |  | PARTIAL | Inventory Growth |  | Repo | 24.0 |  |
| poa | exact |  | True | Percent operating accruals | data_rawa['poa'] = data_rawa['oa']/data_rawa['ni'] | Repo | 35.0 |  |
| em | exact |  | True | Enterprise multiple | data_rawa['em'] = data_rawa['enteprs_v'] / data_rawa['oibdp'] | Repo | 12.0 |  |
| cash | exact |  | True | Cash holdings | data_rawq['cash'] = data_rawq['cheq']/data_rawq['atq'] | Repo | 89.0 |  |
| gma | exact |  | True | Gross profitability | data_rawq['gma'] = (data_rawq['revtq4']-data_rawq['cogsq4'])/data_rawq['atq_l4'] | Repo | 97.0 |  |
| orgcap | exact |  | True | Organizational capital | orgcap_1/avgat | SAS |  | 393.0 |
| hire | exact |  | True | Employee growth rate | data_rawa['hire'] = (data_rawa['emp'] - data_rawa['emp_l1'])/data_rawa['emp_l1'] | Repo | 100.0 |  |
| gad | opensource |  | True | Growth in advertising expense |  | OpenSource |  |  |
| ala | exact |  | True | Adjusted liquid assets | data_rawq['ala'] = data_rawq['cheq'] + 0.75*(data_rawq['actq']-data_rawq['cheq'])+0.5*(data_rawq['atq']-data_rawq['actq']-data_rawq['gdwlq']-data_rawq['intanq']) | Repo_accounting |  |  |
| convind | opensource |  | True | Convertible debt indicator |  | OpenSource |  |  |


