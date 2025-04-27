from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, SocialEvent

# Create a set to store follower user IDs
followers = set()

# Create the client
client: TikTokLiveClient = TikTokLiveClient(unique_id="@calipokehouse")

@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")

async def on_social(event: SocialEvent) -> None:
    print(event.base_message.display_text)
    if "followed" in event.base_message.display_text.default_pattern.lower():
        user_id = event.user.id
        nickname = event.user.nick_name
        
        if user_id not in followers:
            followers.add(user_id)
            print(f"\nNew follower detected!")
            print(f"Username: {nickname}")
            print(f"User ID: {user_id}")
            print(f"Total unique followers in this session: {len(followers)}\n")
        else:
            print(f"{nickname} is already in followers list")


# Add listeners
client.add_listener(SocialEvent, on_social)


if __name__ == '__main__':
    client.run()