import os
import sys
import boto3
from botocore.exceptions import ClientError

def must(name: str) -> str:
    v = os.getenv(name)
    if not v:
        print(f"Missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return v

ACCOUNT_ID = must("R2_ACCOUNT_ID")
ACCESS_KEY = must("R2_ACCESS_KEY_ID")
SECRET_KEY = must("R2_SECRET_ACCESS_KEY")
ENDPOINT = must("R2_ENDPOINT_URL")

BUCKETS = [
    must("R2_BUCKET_STUDENT"),
    must("R2_BUCKET_TEACHER"),
    must("R2_BUCKET_SUBMISSIONS"),
]

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

TEST_KEY = "smoketest/ping.txt"
TEST_BODY = f"ok - {ACCOUNT_ID}\n".encode("utf-8")

def main():
    print("Endpoint:", ENDPOINT)
    ok = True

    for b in BUCKETS:
        print(f"\n== Bucket: {b}")

        try:
            s3.head_bucket(Bucket=b)
            print("  head_bucket: OK")
        except ClientError as e:
            ok = False
            print("  head_bucket: FAIL", e.response.get("Error", {}))
            continue

        try:
            s3.put_object(Bucket=b, Key=TEST_KEY, Body=TEST_BODY, ContentType="text/plain")
            obj = s3.get_object(Bucket=b, Key=TEST_KEY)
            data = obj["Body"].read()
            if data != TEST_BODY:
                raise RuntimeError("GET returned unexpected content")
            s3.delete_object(Bucket=b, Key=TEST_KEY)
            print("  put/get/delete: OK")
        except ClientError as e:
            ok = False
            print("  put/get/delete: FAIL", e.response.get("Error", {}))
        except Exception as e:
            ok = False
            print("  put/get/delete: FAIL", repr(e))

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()