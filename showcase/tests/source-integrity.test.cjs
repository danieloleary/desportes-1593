'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const root=path.resolve(__dirname,'../..'),site=path.join(root,'showcase');
const hash=data=>crypto.createHash('sha256').update(data).digest('hex');
const context={window:{}};vm.runInNewContext(fs.readFileSync(path.join(site,'data.js'),'utf8'),context);const data=context.window.DESPORTES;
test('reader retains exact public French, translation and uncertainty',()=>{
  assert.equal(data.letters.length,2);
  for(const letter of data.letters){
    const raw=fs.readFileSync(path.join(root,'reading',letter.id+'_reading.txt'),'utf8');
    const at=raw.indexOf('\nTRANSLATION');assert(at>0);
    assert.equal(letter.french,raw.slice(0,at).trimEnd());
    assert.equal(letter.english,raw.slice(raw.indexOf('\n',at+1)+1).trim());
    assert(letter.french.includes('(?)'));assert(letter.french.includes('['));
    assert.equal(data.sources['reading/'+letter.id+'_reading.txt'],hash(Buffer.from(raw)));
  }
});
test('manifest and bundle agree with public source bytes',()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(site,'SOURCE_MANIFEST.json')));
  assert.equal(manifest.upstream_commit,data.pin);
  for(const [name,sha] of Object.entries(manifest.files))assert.equal(hash(fs.readFileSync(path.join(root,name))),sha);
});
test('local links and fragments have real targets',()=>{
  const html=fs.readFileSync(path.join(site,'index.html'),'utf8');
  for(const [,url] of html.matchAll(/(?:href|src)="([^"]+)"/g)){
    if(/^(https:|data:)/.test(url))continue;
    if(url.startsWith('#')){assert(html.includes('id="'+url.slice(1)+'"'),url);continue;}
    const target=path.resolve(site,url);assert(target.startsWith(root+path.sep));assert(fs.existsSync(target),url);
  }
});
test('runtime has no new scans, private Site configuration, data transfers or HTML sinks',()=>{
  const html=fs.readFileSync(path.join(site,'index.html'),'utf8'),js=fs.readFileSync(path.join(site,'app.js'),'utf8');
  assert(!/<img\b/i.test(html));assert(!/innerHTML|insertAdjacentHTML|document\.write|\beval\(/.test(js));
  for(const text of [html,js,fs.readFileSync(path.join(site,'data.js'),'utf8')])assert(!/\/Users\/|OAI-Sites-Authorization|siwc_bypass|\.chatgpt\.site/.test(text));
  assert(!/fetch\(|XMLHttpRequest|WebSocket|sendBeacon/.test(js));assert(!fs.existsSync(path.join(site,'.openai')));
});

test('download bytes match the published SHA-256 record',()=>{
  const dir=path.join(site,'downloads'),line=fs.readFileSync(path.join(dir,'SHA256SUMS.txt'),'utf8').trim();
  const [expected,name]=line.split(/\s+/);assert.equal(name,'desportes-saved-verifier.zip');assert.equal(expected,hash(fs.readFileSync(path.join(dir,name))));
  const record=JSON.parse(fs.readFileSync(path.join(site,'evidence/saved-score.json')));assert.equal(record.glyph.edit_errors,4);assert.equal(record.glyph.reference_length,1301);assert.equal(record.letter.edit_errors,23);assert.equal(record.letter.reference_length,1369);assert.equal(record.coverage.excluded_letter_name_placeholders,4);
});
