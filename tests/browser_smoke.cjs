// Requires Playwright + Chromium on the development machine (not end-user PCs).
const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
 const context=await browser.newContext();const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8001/');await page.getByText('준비됐습니다.',{exact:true}).waitFor();
 await page.locator('#text').fill('첫 번째 기사 본문');await page.locator('#analyze').click();await page.locator('#answer').filter({hasText:'첫 번째 기사 본문'}).waitFor();
 await page.locator('#correction').fill('결론 먼저, 근거 세 개');await page.locator('#fix').click();await page.locator('#memories').getByText('웹페이지 핵심 정리',{exact:true}).waitFor();
 await page.reload();await page.getByText('준비됐습니다.',{exact:true}).waitFor();await page.locator('#text').fill('두 번째 기사');await page.locator('#analyze').click();await page.locator('#answer').filter({hasText:'결론 먼저, 근거 세 개'}).waitFor();
 await page.locator('#sync').check();await page.getByText('교정 동기화 완료. 화면·답변·단계 기록은 업로드하지 않았습니다.',{exact:true}).waitFor();
 const other=await browser.newContext();const p2=await other.newPage();await p2.goto('http://127.0.0.1:8001/');await p2.getByText('준비됐습니다.',{exact:true}).waitFor();await p2.locator('#sync').check();await p2.getByText('교정 동기화 완료. 화면·답변·단계 기록은 업로드하지 않았습니다.',{exact:true}).waitFor();if(await p2.locator('#memories textarea').count()!==0)throw Error('cross-browser memory leak');
 const box=page.locator('#memories .memory');await box.locator('textarea').fill('주의점도 포함');await box.getByText('변경 저장',{exact:true}).click();await page.getByText('교정을 수정했습니다. 다음 분석부터 사용합니다.',{exact:true}).waitFor();await page.locator('#analyze').click();await page.locator('#answer').filter({hasText:'주의점도 포함'}).waitFor();
 await box.getByText('삭제',{exact:true}).click();await page.getByText('아직 교정이 없습니다. 답변을 수정하면 여기에 기억합니다.',{exact:true}).waitFor();await page.locator('#analyze').click();await page.locator('#answer').filter({hasText:'데모:'}).waitFor();if((await page.locator('#answer').textContent()).includes('주의점도 포함'))throw Error('deleted memory reused');
 await page.screenshot({path:'/tmp/aihelper-web.png',fullPage:true});
 // Simulate a static host with no backend.
 const staticContext=await browser.newContext();const staticPage=await staticContext.newPage();await staticPage.route('**/api/**',route=>route.fulfill({status:404,body:'not found'}));await staticPage.goto('http://127.0.0.1:8001/');await staticPage.getByText('준비됐습니다.',{exact:true}).waitFor();await staticPage.locator('#text').fill('설치 없는 웹 시험');await staticPage.locator('#analyze').click();await staticPage.locator('#answer').filter({hasText:'설치 없는 웹 시험'}).waitFor();if(!await staticPage.locator('#sync').isDisabled())throw Error('sync enabled on static host');
 if(errors.length)throw Error(errors.join('\n'));
 console.log('Browser PASS: no-screen demo, correction persist/retrieve/edit/delete, opt-in sync, browser isolation, static-host fallback, no JS runtime errors.');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
