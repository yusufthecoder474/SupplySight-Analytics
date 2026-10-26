// Authoring runtime: @oai/artifact-tool. CSV/JSON reports are portable source inputs.
import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.resolve(process.argv[2] || '.');
const data = JSON.parse(await fs.readFile(path.join(root, 'reports/workbook_data.json'), 'utf8'));
const wb = Workbook.create();
const names = ['Executive Summary', 'Inventory Risk', 'Forecast Results', 'Product Master', 'Demand History', 'KPI Validation', 'Data Dictionary'];
for (const n of names) wb.worksheets.add(n);
const col = i => { let s=''; for(i++;i;i=Math.floor((i-1)/26))s=String.fromCharCode(65+(i-1)%26)+s; return s; };
const header = (sheet, range) => { sheet.getRange(range).format = {fill:'#17324D',font:{name:'Arial',bold:true,color:'#FFFFFF',size:10},rowHeight:32,wrapText:true,horizontalAlignment:'center'}; };
for (const n of names) {
  const s=wb.worksheets.getItem(n);s.showGridLines=false;
  s.getRange('A1:Q30').format.font={name:'Arial',size:10,color:'#17324D'};
  s.getRange('A2').values=[[n === 'Executive Summary' ? 'SupplySight Operations Analysis' : n]];
  s.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:'#17324D'};
  s.getRange('A3').values=[[n==='Inventory Risk'?'SYNTHETIC planning scenario. Editable inputs E:H. Historical demand C:D.': n==='Demand History'?'Source: Chen (2015), UCI Online Retail, CC BY 4.0. doi.org/10.24432/C5BW33':n==='Executive Summary'?'Historical retail sales, Dec 2010–Nov 2011. Inventory and capacity are synthetic.':'Generated from the executed SupplySight pipeline. See docs for definitions.']];
  s.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:'#64748B'};
  if (n==='Executive Summary') continue;
  const t=data[n], rows=t.rows.map(row=>row.map((v,i)=>['date','train_end','as_of'].includes(t.columns[i])&&v?new Date(v):v));
  const end=rows.length+5, last=col(t.columns.length-1);
  s.getRange(`A5:${last}${end}`).values=[t.columns,...rows];
  s.getRange(`A5:${last}${end}`).format.font={name:'Arial',size:10,color:'#17324D'};
  s.getRange(`A5:${last}${end}`).format.rowHeight=20;
  s.getRange(`A5:${last}${end}`).format.columnWidth=18;
  header(s,`A5:${last}5`);
  s.tables.add(`A5:${last}${end}`,true,n.replaceAll(' ','')+'Table');
  s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(1);
  t.columns.forEach((c,i)=>{
    const rg=s.getRange(`${col(i)}6:${col(i)}${end}`);
    if(['date','train_end','as_of'].includes(c))rg.setNumberFormat('dd-mmm-yy');
    else if(rows.some(r=>typeof r[i]==='number'))rg.setNumberFormat('#,##0.00');
  });
  if(n==='Product Master'){s.getRange('B5:B25').format.columnWidth=48;}
  if(n==='Demand History')s.getRange(`C6:C${end}`).setNumberFormat('#,##0');
  if(n==='Data Dictionary'){s.getRange(`C5:C${end}`).format.columnWidth=40;s.getRange(`B5:B${end}`).format.columnWidth=48;s.getRange(`F5:F${end}`).format.columnWidth=80;}
  if(n==='Inventory Risk'){
    s.getRange('Q5').values=[['description']];header(s,'Q5');s.getRange('Q5:Q25').format.columnWidth=48;
    const formulas=[];
    for(let r=6;r<=end;r++){
      formulas.push([`=IF(C${r}=0,"",E${r}/C${r})`,`=H${r}*F${r}+1.65*D${r}*SQRT(F${r})`,`=IF(E${r}<J${r},1,0)`,`=IF(C${r}=0,0,IF(I${r}>60,1,0))`,`=H${r}*7/G${r}`,`=IF(C${r}=0,"",D${r}/C${r})`]);
      s.getRange(`Q${r}`).formulas=[[`=_xlfn.XLOOKUP(A${r},'Product Master'!$A$6:$A$25,'Product Master'!$B$6:$B$25,"Missing product")`]];
    }
    s.getRange(`I6:N${end}`).formulas=formulas;
    s.getRange(`M6:O${end}`).setNumberFormat('0.0%');
    s.getRange(`E6:H${end}`).format.fill='#FFF3CD';
    s.getRange(`E6:E${end}`).dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
    s.getRange(`H6:H${end}`).dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
    s.getRange(`F6:G${end}`).dataValidation={rule:{type:'decimal',operator:'greaterThan',formula1:0}};
    s.getRange(`K6:K${end}`).conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:'#FEE2E2',font:{color:'#B91C1C'}}});
    s.getRange(`I6:I${end}`).conditionalFormats.add('cellIs',{operator:'greaterThan',formula:60,format:{fill:'#FEF3C7'}});
    s.getRange('P5:P25').format.columnWidth=64;
  }
  if(n==='Forecast Results'){
    s.getRange(`H6:I${end}`).formulas=rows.map((_,i)=>{const r=i+6;return [`=ABS(G${r}-F${r})`,`=G${r}-F${r}`];});
  }
  if(n==='KPI Validation'){
    s.getRange('A5:A20').format.columnWidth=28;
    s.getRange(`D6:E${end}`).formulas=rows.map((_,i)=>{const r=i+6;return [`=C${r}-B${r}`,`=ABS(D${r})<0.000001`];});
    s.getRange(`E6:E${end}`).conditionalFormats.add('cellIs',{operator:'equal',formula:'FALSE',format:{fill:'#FEE2E2'}});
  }
}
const s=wb.worksheets.getItem('Executive Summary');s.tabColor='#17324D';
s.getRange('A5:B5').values=[['Measure','Value']];header(s,'A5:B5');
s.getRange('A6:A10').values=[['Total sales units'],['Products monitored'],['At-risk products (synthetic)'],['Overstock products (synthetic)'],['Mean days cover (synthetic)']];
const n=data['Demand History'].rows.length+5;
s.getRange('B6:B10').formulas=[['=SUM(\'Demand History\'!C6:C'+n+')'],["=COUNTA('Product Master'!A6:A25)"],["=SUM('Inventory Risk'!K6:K25)"],["=SUM('Inventory Risk'!L6:L25)"],["=AVERAGE('Inventory Risk'!I6:I25)"]];
s.getRange('A5:A10').format.columnWidth=37;s.getRange('B5:B10').format.columnWidth=18;s.getRange('B6:B9').setNumberFormat('#,##0');s.getRange('B10').setNumberFormat('#,##0.0');
s.getRange('A13:D13').values=[['Model','MAE units','WAPE','Bias']];header(s,'A13:D13');
for(let i=0;i<3;i++){
  const r=i+14, model=data.comparison[i][0], end=data['Forecast Results'].rows.length+5;
  s.getRange(`A${r}`).values=[[model]];
  s.getRange(`B${r}:D${r}`).formulas=[[
    `=AVERAGEIF('Forecast Results'!$E$6:$E$${end},A${r},'Forecast Results'!$H$6:$H$${end})`,
    `=SUMIF('Forecast Results'!$E$6:$E$${end},A${r},'Forecast Results'!$H$6:$H$${end})/SUMIF('Forecast Results'!$E$6:$E$${end},A${r},'Forecast Results'!$F$6:$F$${end})`,
    `=SUMIF('Forecast Results'!$E$6:$E$${end},A${r},'Forecast Results'!$I$6:$I$${end})/SUMIF('Forecast Results'!$E$6:$E$${end},A${r},'Forecast Results'!$F$6:$F$${end})`]];
}
s.getRange('B14:B16').setNumberFormat('#,##0.0');s.getRange('C14:D16').setNumberFormat('0.0%');s.getRange('C5:D16').format.columnWidth=16;
s.getRange('A19').values=[['Planning uses seasonal-naive, chosen before holdout evaluation.']];
s.getRange('A20').values=[['Change scenario inputs on Inventory Risk to review flags.']];
const ch=s.charts.add('bar',[s.getRange('A13:A16'),s.getRange('C13:C16')]);ch.title='Backtest WAPE';ch.setPosition('F5','N19');ch.hasLegend=false;
ch.yAxis={numberFormatCode:'0%',numberFormatSourceLinked:false};ch.series.items[0].fill='#0D9488';
wb.recalculate();
const before=wb.worksheets.getItem('Inventory Risk').getRange('I6').values[0][0];
const inputs=wb.worksheets.getItem('Inventory Risk').getRange('E6');const original=inputs.values[0][0];
inputs.values=[[original+100]];wb.recalculate();
const after=wb.worksheets.getItem('Inventory Risk').getRange('I6').values[0][0];
if(before===after)throw new Error('Scenario input did not recalculate days cover');
inputs.values=[[original]];wb.recalculate();
const errs=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!',options:{useRegex:true,maxResults:30},maxChars:3000});
console.log(errs.ndjson);
console.log((await wb.inspect({kind:'table',range:'Executive Summary!A5:D16',include:'values,formulas',tableMaxRows:12,tableMaxCols:4,maxChars:3000})).ndjson);
await fs.mkdir(path.join(root,'excel'),{recursive:true});
for(const n of names){
  const ranges=n==='Executive Summary'?['A1:N22']:n==='Inventory Risk'?['A1:H14','I5:Q14']:['A1:'+({ 'Product Master':'B', 'Demand History':'C', 'Forecast Results':'I', 'KPI Validation':'E', 'Data Dictionary':'E'}[n])+'14'];
  for(let i=0;i<ranges.length;i++){
    const image=await wb.render({sheetName:n,range:ranges[i],scale:1.5,format:'png'});
    await fs.writeFile(path.join(root,'docs/screenshots',`workbook_${n.replaceAll(' ','_')}_${i}.png`),new Uint8Array(await image.arrayBuffer()));
  }
}
const file=await SpreadsheetFile.exportXlsx(wb);await file.save(path.join(root,'excel/SupplySight_Operations_Analysis.xlsx'));
console.log('Workbook exported; scenario recalculation verified');
