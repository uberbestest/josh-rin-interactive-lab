from pathlib import Path
import json,datetime,hashlib
from playwright.sync_api import sync_playwright
root=Path(__file__).parent
pagepath=root/'The_Test_That_Watched_Back_Explorer.html'
checks=[];errors=[];network=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    for width,height,tag in [(1365,1000,'desktop'),(390,844,'mobile')]:
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.on('request',lambda req:network.append(req.url))
        # Render the already-authored document; do not ask the browser to access a local file.
        page.set_content(pagepath.read_text(encoding='utf-8'),wait_until='load')
        page.wait_for_selector('#policy-results tbody tr')
        assert page.locator('#policy-results tbody tr').count()==6
        no_overflow=page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        checks.append({'viewport':tag,'width':width,'height':height,'no_page_overflow':no_overflow,'policy_rows':6,'presentation_render':'PASS','local_file_launch':'UNQUALIFIED: file URI blocked by administrator'})
        assert no_overflow, f'page overflow at {tag}'
        before=page.locator('#policy-results tbody tr').nth(3).locator('td').nth(1).inner_text()
        assert before.startswith('1') and 'Truthful' in before
        page.locator('#flip-future').click()
        after=page.locator('#policy-results tbody tr').nth(3).locator('td').nth(1).inner_text()
        assert after.startswith('0') and 'False report' in after
        twin=page.locator('#policy-results tbody tr').nth(4).locator('td').nth(1).inner_text()
        assert twin==after
        page.locator('#suite').select_option('challenge')
        assert page.locator('#flip-future').is_disabled()
        assert page.locator('#audit option').count()==4
        assert page.locator('#policy-results tbody tr').count()==6
        page.locator('#load-witness').click()
        assert page.locator('#suite').input_value()=='primary'
        assert page.locator('#continuation').input_value()=='6'
        assert page.locator('#panel-signatures tr').count()==6
        # Exhaustively verify displayed reports and raw fractions against the embedded retained data.
        result=page.evaluate('''() => {
          let contexts=0, reports=0;
          for(const [id,c] of Object.entries(DATA.contexts)) {
            let suite=id.startsWith('primary')?'primary':'challenge';
            document.getElementById('suite').value=suite;configure(suite,c.view);
            let rr=document.querySelectorAll('#policy-results tbody tr');
            for(let i=0;i<6;i++){
              let td=rr[i].querySelectorAll('td');
              if(td[1].querySelector('strong').textContent!==String(c.policies[i].report))throw Error('report mismatch '+id);
              if(td[2].querySelector('small').textContent!==c.policies[i].pass)throw Error('pass mismatch '+id);
              reports++;
            } contexts++;
          }
          return {contexts,reports};
        }''')
        assert result=={'contexts':432,'reports':2592}
        checks[-1].update({'future_witness_toggle':'PASS','lookup_equality':'PASS','suite_switch':'PASS','minimum_panel_rows':6,'retained_case_display_checks':result})
        page.locator('#load-witness').click()
        page.evaluate('window.scrollTo(0,0)')
        page.screenshot(path=str(root/'verification'/f'explorer_{tag}_top.png'),full_page=False)
        page.locator('.lab').screenshot(path=str(root/'verification'/f'explorer_{tag}_controls.png'))
        page.close()
    browser.close()
assert not errors,errors
external=[u for u in network if not u.startswith('file://')]
assert not external,external
receipt={'status':'PASS','checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'javascript_errors':errors,'external_requests':external,'html_sha256':hashlib.sha256(pagepath.read_bytes()).hexdigest(),'qualification':'Chromium/Linux rendering of the supplied authored HTML string at two viewport sizes. Direct file-URI launch was blocked and is unqualified; no browser policy change or host-route retry. Not native Windows or all mobile browsers.'}
(root/'verification/browser_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
