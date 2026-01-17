import json
import argparse
import sys
import os
import urllib.request
import urllib.error

# Function: submit_request
# Complexity: Cyclomatic=5 (1 try-except + 2 if checks + 1 loop + 1 function call)
# Lines: 45
def submit_request(env, source, target, rpc_meta_list, zones, jwt_token, cookie=None):
    """
    Submits a batch ACL application request to Neptune for a specific (source, target) pair.
    """
    env_map = {
        "BOE": "cloud-boe.bytedance.net",
        "Online-CN": "cloud.bytedance.net",
        "i18n-BD": "cloud.byteintl.net"
    }
    
    domain = env_map.get(env)
    if not domain:
        print(f"错误: 不支持的环境 '{env}'。可用环境: {list(env_map.keys())}", file=sys.stderr)
        return False

    url = f"https://{domain}/api/v1/neptune/api/neptune/acl/strict_authorization/apply/downstream/batch"
    
    # Handle zones as comma-separated string or list
    if isinstance(zones, str):
        zone_list = [z.strip() for z in zones.split(",")]
    else:
        zone_list = zones

    # In batch mode, we use the first target cluster as the main cluster if not provided
    main_cluster = rpc_meta_list[0]["callee_cluster"] if rpc_meta_list else "default"

    payload = {
        "approval_mode": "",
        "cluster": main_cluster,
        "down_stream_list": [],
        "psm": target,
        "rpc_meta_list": rpc_meta_list,
        "usage_scenario": "ACL apply via Coco (batch-optimized)",
        "zones": zone_list
    }

    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "x-jwt-token": jwt_token,
        "Origin": f"https://{domain}",
        "Referer": f"https://{domain}/neptune/secure/acl/apply",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    if cookie:
        headers["Cookie"] = cookie
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        methods = list(set([m["method"] for m in rpc_meta_list]))
        clusters = list(set([m["callee_cluster"] for m in rpc_meta_list]))
        print(f"[{env}] 正在提交申请: {source} -> {target} | 集群: {clusters} | 方法: {methods}...")
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            print(f"[{env}] Neptune 响应成功!")
            return True
    except urllib.error.HTTPError as e:
        print(f"[{env}] HTTP 错误: {e.code} {e.reason}", file=sys.stderr)
        err_msg = e.read().decode('utf-8')
        print(f"错误内容: {err_msg}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[{env}] 发生意外错误: {e}", file=sys.stderr)
        return False

def parse_list(s):
    if not s:
        return []
    return [item.strip() for item in s.split(",") if item.strip()]

def main():
    parser = argparse.ArgumentParser(description="Apply for Neptune ACL (Batch Optimized)")
    
    # Core Arguments
    parser.add_argument("--env", choices=["BOE", "Online-CN", "i18n-BD"], default="BOE", help="Target environment")
    parser.add_argument("--source", help="Source PSM (Caller), supports multiple comma-separated")
    parser.add_argument("--source-cluster", default="default", help="Source cluster(s), supports multiple comma-separated")
    parser.add_argument("--target", help="Target PSM (Callee), supports multiple comma-separated")
    parser.add_argument("--target-cluster", default="default", help="Target cluster(s), supports multiple comma-separated")
    parser.add_argument("--zones", default="BOE", help="Zones (comma separated)")
    parser.add_argument("--method", required=True, help="RPC Method path(s), supports multiple comma-separated")
    
    # Compatibility aliases
    parser.add_argument("--caller", help="Alias for --source")
    parser.add_argument("--callee", help="Alias for --target")
    parser.add_argument("--cluster", help="Sets both --source-cluster and --target-cluster (comma-separated)")

    # Auth
    parser.add_argument("--jwt", help="Neptune x-jwt-token (or NEPTUNE_JWT env)")
    parser.add_argument("--cookie", help="Neptune Cookie (or NEPTUNE_COOKIE env)")

    args = parser.parse_args()
    
    # Resolve and parse lists
    source_str = args.source or args.caller
    target_str = args.target or args.callee
    
    if not source_str or not target_str:
        print("错误: 必须指定 --source (或 --caller) 和 --target (或 --callee)", file=sys.stderr)
        sys.exit(1)
        
    source_list = parse_list(source_str)
    target_list = parse_list(target_str)
    
    source_cluster_list = parse_list(args.source_cluster)
    target_cluster_list = parse_list(args.target_cluster)
    
    if args.cluster:
        c_list = parse_list(args.cluster)
        source_cluster_list = c_list
        target_cluster_list = c_list
        
    method_list = parse_list(args.method)
    
    jwt = args.jwt or os.environ.get("NEPTUNE_JWT")
    cookie = args.cookie or os.environ.get("NEPTUNE_COOKIE")
    
    if not jwt:
        print("错误: 缺少 x-jwt-token。请通过 --jwt 或环境变量 NEPTUNE_JWT 指定。", file=sys.stderr)
        sys.exit(1)

    # Process each (source, target) pair
    for s in source_list:
        for t in target_list:
            # Construct rpc_meta_list for this pair
            rpc_meta_list = []
            for sc in source_cluster_list:
                for tc in target_cluster_list:
                    # Usually caller_cluster and callee_cluster are correlated in common scenarios, 
                    # but here we allow Cartesian product if they are different lists.
                    # If they are intended to be 1:1, use a single --cluster instead.
                    for m in method_list:
                        rpc_meta_list.append({
                            "caller": s,
                            "caller_cluster": sc,
                            "callee": t,
                            "callee_cluster": tc,
                            "method": m
                        })
            
            if not rpc_meta_list:
                continue

            # Standard application
            success = submit_request(args.env, s, t, rpc_meta_list, args.zones, jwt, cookie)
            
            # Pre-release application (if not BOE)
            if success and args.env != "BOE":
                s_pre = s + "_pre_release"
                t_pre = t + "_pre_release"
                print(f"\n[{args.env}] 检测到非 BOE 环境，自动发起 Pre-release 申请: {s_pre} -> {t_pre}...")
                
                rpc_meta_pre = []
                for item in rpc_meta_list:
                    new_item = item.copy()
                    new_item["caller"] = s_pre
                    new_item["callee"] = t_pre
                    rpc_meta_pre.append(new_item)
                
                submit_request(args.env, s_pre, t_pre, rpc_meta_pre, args.zones, jwt, cookie)

if __name__ == "__main__":
    main()
