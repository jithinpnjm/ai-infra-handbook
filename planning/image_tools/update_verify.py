with open("verify_timeline.py") as f:
    text = f.read()

# Replace padding check logic to check each line (tspan or text)
old_code = """            texts = el.findall('{http://www.w3.org/2000/svg}text')
            msg_el = texts[-1]
            t = "".join(msg_el.itertext()).strip()
            bw = float(rect.attrib['width'])
            fs = float(msg_el.attrib['font-size'])
            est_w = len(t) * 0.6 * fs
            pad = (bw - est_w) / 2
            print(f"   [{gid}] '{t[:35]}...' bw={bw} est_w={est_w:.1f} pad={pad:.1f}px")
            assert pad >= 16.0, f"Card padding {pad} < 16 for '{t}'!\""""

new_code = """            texts = el.findall('{http://www.w3.org/2000/svg}text')
            msg_el = texts[-1]
            bw = float(rect.attrib['width'])
            fs = float(msg_el.attrib['font-size'])
            tspans = msg_el.findall('{http://www.w3.org/2000/svg}tspan')
            if len(tspans) > 0:
                for tsp in tspans:
                    ltxt = tsp.text.strip()
                    est_w = len(ltxt) * 0.6 * fs
                    pad = (bw - est_w) / 2
                    print(f"   [{gid} line] '{ltxt}' bw={bw} est_w={est_w:.1f} pad={pad:.1f}px")
                    assert pad >= 16.0, f"Line padding {pad} < 16 for '{ltxt}'!"
            else:
                t = msg_el.text.strip()
                est_w = len(t) * 0.6 * fs
                pad = (bw - est_w) / 2
                print(f"   [{gid}] '{t[:35]}...' bw={bw} est_w={est_w:.1f} pad={pad:.1f}px")
                assert pad >= 16.0, f"Card padding {pad} < 16 for '{t}'!\""""

assert old_code in text
text = text.replace(old_code, new_code)
with open("verify_timeline.py", "w") as f:
    f.write(text)
print("Updated verify_timeline.py")
