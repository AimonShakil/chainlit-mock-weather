import os
import chainlit as cl 
# for creating conversational UI Interface

from agents import Agent, Runner, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, function_tool
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

gemini_api_key= os.getenv("GEMINI_API_KEY")

# Step 1: Provider
provider = AsyncOpenAI(     # provider/ client/ extrenal client
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

# step 2: Model Selection
model=OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=provider
)

# Step 3: Defining Config at run level - Working a run level for this project
run_config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True
)

# Hardcoded Cities and mock weather data

MOCK_WEATHER_DATA = {
    "london": "sunny with 25°C",
    "new york": "cloudy with 18°C",
    "tokyo": "rainy with 22°C",
    "paris": "partly cloudy with 20°C",
    "sydney": "warm with 30°C",
}

@function_tool
def weather_lookup_tool(city_name: str) -> str:
    """
    Returns weather information for a given city from a mock dataset.

    Args:
        city_name: The name of the city (e.g., "london", "new york").

    Returns:
        A string describing the weather for the city, or a "not found" message
        if the city is not in the mock data.
    """
    if city_name in MOCK_WEATHER_DATA:
        weather_info = MOCK_WEATHER_DATA[city_name]
        return f"The weather in {city_name} is {weather_info} "
    else:
        # This part of the logic is now handled inside the tool,
        # making the tool more self-contained.
        known_cities = " , ".join([city.title() for city in MOCK_WEATHER_DATA.keys()])
        return (
            f"I'm sorry, I dont have weather information for {city_name.title()}."
            f"Please ask me about: {known_cities}"
        )
# Step 4 Creating an Agent 
'''
A bot that can "look up" weather information for a few hardcoded cities. Instead of a real API, we'll have static
responses for specific city names.
'''
agent = Agent(
    name="Weather Assistant",
    instructions="you are a helpful assistant that can look up weather information for few hardcoded cities in MOCK_WEATHER_DATA",
    tools=[weather_lookup_tool]
)


# we will up our server with this custom file
# Chainlit intigration starts here.
# we want as user sends a message,
# through runner it runs asynchronous and it's answer should return in repsonse 
# --------------------

# to maintain a chat history, it creates a user session as
# chat starts ad sets a variable history on closing hsitory will be removed/ temporary not persistent.
# [{" role" : "user", "content": "hello"}]

@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hi! I am a simple weather Bot. ask me about the weather in renowned cities of the world! 😊").send()

@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    
    history.append({"role": "user", "content": message.content})
    result = await Runner.run(agent,
    input=history,
    run_config=run_config, 
    # The "agentic Element: Identify the "  
)
    
    history.append({"role": "user", "content": result.final_output})
    cl.user_session.set("history", history)
    await cl.Message(content=result.final_output).send()

