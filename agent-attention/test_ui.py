#!/usr/bin/env python3
"""Actual Chromium checks for the mapped public site, served from localhost."""
import contextlib
import http.server
import json
import socketserver
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent.parent
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def log_message(self,*args):pass

errors=[]
checks=[]
with socketserver.TCPServer(("127.0.0.1",0),Handler) as server:
    server.allow_reuse_address=True
    th=threading.Thread(target=server.serve_forever,daemon=True)
    th.start()
    base="http://127.0.0.1:"+str(server.server_address[1])
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        for width in [320,390,768,1440]:
            page=browser.new_page(viewport={"width":width,"height":850},reduced_motion="reduce")
            page.on("pageerror",lambda e:errors.append(str(e)))
            response=page.goto(base+"/agent-attention/index.html",wait_until="load")
            assert response.status==200
            assert "Agent Attention" in page.title()
            assert page.locator("#eventNav button").count()==15
            assert page.locator("#detailMeta").inner_text().startswith("E01")
            page.locator("#next").click()
            assert page.locator("#detailMeta").inner_text().startswith("E02")
            page.locator("#eventNav button").nth(10).click()
            assert page.locator("#detailStatus").inner_text().startswith("Search-only")
            page.locator("#branchFilter").select_option("caution")
            assert page.locator("#traceGraph .pointGroup").count()==15
            assert page.locator("#traceGraph .pointGroup").nth(10).evaluate("(e)=>e.style.opacity")=="1"
            assert abs(float(page.locator("#traceGraph .pointGroup").nth(1).evaluate("(e)=>e.style.opacity"))-0.16)<1e-6
            page.locator("#eventNav button").nth(14).click()
            assert "N03" in page.locator("#detailNote").inner_text()
            page.locator("#witnessChoice").select_option("seed72")
            assert "Sixteen" in page.locator("#witnessText").inner_text()
            assert "16" in page.locator("#witnessBars").inner_text()
            page.locator("#witnessChoice").select_option("seed4")
            assert "Lantern" in page.locator("#witnessText").inner_text()
            overflow=page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
            assert overflow<=1,("Page overflow",width,overflow)
            methods=page.goto(base+"/agent-attention/method.html")
            assert methods.status==200
            assert page.locator("#pilot").count()==1
            checks.append({"viewport":width,"result":"PASS","overflow_px":overflow})
            page.close()
        browser.close()
    server.shutdown()
assert not errors,errors
print(json.dumps({"browser":"headless Chromium, localhost HTTP","status":"PASS","screens":checks,"javascript_errors":errors},indent=2))
