import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const root=process.argv[2];
const data=JSON.parse(await fs.readFile(root+'/reports/enhancement/workbook_enhancement.json','utf8'));
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(root+'/reports/archive/original/SupplySight_Operations_Analysis.xlsx'));
console.log((await wb.inspect({kind:'sheet',include:'id,name',maxChars:2000})).ndjson);
const beforeImage=await wb.render({sheetName:'Executive Summary',range:'A1:N22',scale:1.3,format:'png'});
await fs.writeFile(root+'/reports/enhancement/workbook_before.png',new Uint8Array(await beforeImage.arrayBuffer()));
const before=[];
for(let i=0;i<7;i++){const s=wb.worksheets.getItemAt(i);before.push({name:s.name,formulas:s.getUsedRange().formulas});}
const cap=wb.worksheets.add('Capacity Planning');
const study=wb.worksheets.add('Forecast Study');
for(const s of [cap,study]){
 s.showGridLines=false;s.getRange('A1:P28').format.font={name:'Arial',size:10,color:'#17324D'};
 s.getRange('A1:P28').format.columnWidth=17;s.getRange('A2').format.font={name:'Arial',size:16,bold:true};
 s.freezePanes.freezeRows(5);
}
function header(s,r){s.getRange(r).format={fill:'#17324D',font:{name:'Arial',bold:true,color:'#FFFFFF',size:10},rowHeight:36,wrapText:true,horizontalAlignment:'center'};}
cap.getRange('A2').values=[['Weekly capacity and stock exceptions']];
cap.getRange('A3').values=[['SYNTHETIC scenario. Linked to editable inputs on Inventory Risk. Units per week.']];
cap.getRange('A5:P5').values=[['Product','Weekly demand','Weekly capacity','Demand / capacity','Shortfall flag','Shortfall units','On hand','Lead days','Daily forecast','Daily std dev','Lead demand','Lead stock risk','Forecast cover days','Reorder threshold','Reorder flag','Any exception']];header(cap,'A5:P5');
let formulas=[];
for(let r=6;r<=25;r++)formulas.push([
 `='Inventory Risk'!A${r}`,`=I${r}*7`,`='Inventory Risk'!G${r}`,`=B${r}/C${r}`,`=IF(B${r}>C${r},1,0)`,`=MAX(0,B${r}-C${r})`,
 `='Inventory Risk'!E${r}`,`='Inventory Risk'!F${r}`,`='Inventory Risk'!H${r}`,`='Inventory Risk'!D${r}`,`=I${r}*H${r}`,`=IF(G${r}<K${r},1,0)`,`=IF(I${r}=0,"",G${r}/I${r})`,`=K${r}+1.65*J${r}*SQRT(H${r})`,`=IF(G${r}<N${r},1,0)`,`=IF(E${r}+L${r}+O${r}>0,1,0)`]);
cap.getRange('A6:P25').formulas=formulas;
cap.getRange('B6:P25').setNumberFormat('#,##0.0');cap.getRange('D6:D25').setNumberFormat('0.0%');
cap.tables.add('A5:P25',true,'CapacityPlanningTable');
for(const c of ['E','L','O','P']){cap.getRange(`${c}6:${c}25`).setNumberFormat('0');cap.getRange(`${c}6:${c}25`).conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:'#FEE2E2',font:{color:'#B91C1C'}}});}
cap.getRange('A28').values=[['Cover uses forecast demand. Inventory Risk retains historical cover. Equality does not flag.']];
study.getRange('A2').values=[['Forecast comparison on reused historical periods']];
study.getRange('A3').values=[['All 20 products. Three rolling origins, 14 days each. No holdout tuning.']];
study.getRange('A5:D5').values=[['Model','MAE units','WAPE','Bias']];header(study,'A5:D5');
study.getRange('A6:D9').values=data.pooled.map(x=>[x.model,x.mae,x.wape,x.bias]);
study.getRange('A5:A9').format.columnWidth=23;study.getRange('B6:B9').setNumberFormat('0.0');study.getRange('C6:D9').setNumberFormat('0.00%');
study.getRange('A11').values=[['Negative bias means underforecasting. Croston SBA alpha is fixed at 0.1.']];
const b=study.charts.add('bar',[study.getRange('A5:A9'),study.getRange('C5:C9')]);b.title='Pooled WAPE';b.hasLegend=false;b.yAxis={numberFormatCode:'0%',numberFormatSourceLinked:false};b.setPosition('F5','M16');
study.getRange('A18:F18').values=[['Target date','Actual units','Croston SBA','Naive','Ridge','Seasonal naive']];header(study,'A18:F18');
study.getRange('A19:F32').values=data.forecast.map(x=>[x.date,x.actual,x.croston_sba,x.naive,x.ridge,x.seasonal_naive]);
study.getRange('B19:F32').setNumberFormat('#,##0');
const ch=study.charts.add('line',study.getRange('A18:F32'));ch.title='Final-origin total units across all products';ch.setPosition('H18','Q34');
ch.xAxis={axisType:'textAxis',textStyle:{fontSize:10}};ch.yAxis={numberFormatCode:'#,##0',numberFormatSourceLinked:false};
const colors=['#17324D','#F59E0B','#94A3B8','#2563EB','#0D9488'];ch.series.items.forEach((s,i)=>{s.line={fill:colors[i],style:'solid',width:2};});
study.getRange('A35:G35').values=[['Product','Model','MAE units','WAPE','Bias','Actual units','Underforecast units']];header(study,'A35:G35');
study.getRange('A36:G115').values=data.product.map(x=>[x.product_id,x.model,x.mae,x.wape,x.bias,x.actual_units,x.underforecast_units]);
study.getRange('B35:B115').format.columnWidth=22;study.getRange('C36:G115').setNumberFormat('#,##0.0');study.getRange('D36:E115').setNumberFormat('0.00%');
study.tables.add('A35:G115',true,'ProductStudyScores');
const sum=wb.worksheets.getItem('Executive Summary');sum.getRange('A23:A25').values=[['Capacity shortfalls (synthetic)'],['Lead-time stock risks (synthetic)'],['Any planning exception (synthetic)']];
sum.getRange('B23:B25').formulas=[["=SUM('Capacity Planning'!E6:E25)"],["=SUM('Capacity Planning'!L6:L25)"],["=SUM('Capacity Planning'!P6:P25)"]];
sum.getRange('A23:B25').format.rowHeight=24;sum.getRange('B23:B25').setNumberFormat('0');
wb.recalculate();
if(sum.getRange('B23:B25').values.flat().join(',')!=='5,6,10')throw Error('Scenario summary differs from Python');
const inv=wb.worksheets.getItem('Inventory Risk');let original=inv.getRange('G6').values[0][0];
inv.getRange('G6').values=[[1]];wb.recalculate();if(cap.getRange('E6').values[0][0]!==1)throw Error('Capacity edit did not update shortfall');
inv.getRange('G6').values=[[original]];let stock=inv.getRange('E6').values[0][0];inv.getRange('E6').values=[[0]];wb.recalculate();if(cap.getRange('L6').values[0][0]!==1)throw Error('Stock edit did not update risk');inv.getRange('E6').values=[[stock]];wb.recalculate();
for(const old of before){const now=wb.worksheets.getItem(old.name).getUsedRange().formulas;for(let r=0;r<old.formulas.length;r++)for(let c=0;c<old.formulas[r].length;c++){if(old.formulas[r][c]&&old.formulas[r][c]!==now[r][c])throw Error(`Changed original formula ${old.name} ${r} ${c}`);}}
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},maxChars:2000})).ndjson);
console.log((await wb.inspect({kind:'table',range:'Executive Summary!A23:B25',include:'values,formulas',maxChars:2000})).ndjson);
for(const [sheet,range,file] of [['Executive Summary','A1:N26','summary'],['Capacity Planning','A1:H16','capacity'],['Capacity Planning','I5:P16','stock'],['Forecast Study','A1:M16','study'],['Forecast Study','A18:Q34','forecast']]){
 const blob=await wb.render({sheetName:sheet,range,scale:1.5,format:'png'});await fs.writeFile(root+'/reports/enhancement/workbook_'+file+'.png',new Uint8Array(await blob.arrayBuffer()));
}
const x=await SpreadsheetFile.exportXlsx(wb);await x.save(root+'/excel/SupplySight_Operations_Analysis.xlsx');
console.log('Exported with original formulas preserved and scenario dependencies tested.');
