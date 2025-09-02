import pocket

pocket_instance = pocket.Pocket(
    consumer_key="114267-ec680a6496fece268c06c57",
    access_token="db05967f-c174-c500-a513-e55458",
)
try:
    response = pocket_instance.get(count=1, detailType="complete", state="all")
    print(response)
except pocket.RateLimitException as e:
    print(f"Rate limit error: {str(e)}")
except Exception as e:
    print(f"Error: {str(e)}")
