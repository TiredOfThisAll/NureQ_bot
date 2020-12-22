from urllib.request import urlopen

response = urlopen("https://randomuser.me/api")
response_content = response.read()
print(response_content)

