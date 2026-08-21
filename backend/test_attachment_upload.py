import io
import json
import datetime
import requests

BASE = "http://127.0.0.1:5000"

def login(username, password):
    r = requests.post(f"{BASE}/api/auth/login", json={"username": username, "password": password})
    ok = r.status_code == 200 and r.json().get("success")
    return (r.json()["data"]["access_token"], r.json()["data"]["user"]) if ok else (None, None)

def get_order_no(token):
    r = requests.get(f"{BASE}/api/visiray/purchase-orders")
    data = r.json()
    items = (data.get("data") or {}).get("items") or []
    if items:
        return items[0]["purchase_order_no"]
    today = datetime.date.today().strftime("%Y-%m-%d")
    fd = {
        "product_code": "TEST-CODE",
        "product_name": "测试产品",
        "quantity": "1",
        "unit": "个",
        "product_type": "测试",
        "receiving_time": today,
        "status": "待入库",
        "supplier": "测试供应商"
    }
    r2 = requests.post(f"{BASE}/api/visiray/purchase-orders", data=fd)
    j = r2.json()
    return (j.get("data") or {}).get("purchase_order_no")

def list_attachments(order_no, token):
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE}/api/visiray/purchase-orders/{order_no}/attachments", headers=h)
    return r.status_code, r.text

def upload_attachment(order_no, token):
    h = {"Authorization": f"Bearer {token}"}
    buf = io.BytesIO(b"hello")
    files = [("files", ("hello.txt", buf, "text/plain"))]
    r = requests.post(f"{BASE}/api/visiray/purchase-orders/{order_no}/attachments", headers=h, files=files)
    return r.status_code, r.text

def run(username, password):
    token, user = login(username, password)
    print(json.dumps({"login_user": user}, ensure_ascii=False))
    if not token:
        print("登录失败")
        return
    order = get_order_no(token)
    print("order_no=", order)
    s1, t1 = list_attachments(order, token)
    print("list_attachments:", s1, t1)
    s2, t2 = upload_attachment(order, token)
    print("upload_attachment:", s2, t2)

if __name__ == "__main__":
    print("== admin ==")
    run("xurenjie", "Visiray88")
    # print("== test ==")
    # run("test", "test123")
