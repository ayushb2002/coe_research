import requests

base = "http://127.0.0.1:5000/"


def test_add():
    response = requests.post(
        base + "add", json={'id': '2', 'title': 'Write a blog post'})
    response.raise_for_status()  # raises exception when not a 2xx response
    if response.status_code != 204:
        return response.json()

    return False


def main():
    res = test_add()
    print(res)


if __name__ == "__main__":
    main()
