import shodan;

sd = "ZGPti2tIIZakDP9qrAIzPmdkyfz3DOp7"

api = shodan.Shodan(sd)

try:
    results = api.search("camera france")
    
    print(results['matches'][0])

except shodan.APIError as e:
    print(e)