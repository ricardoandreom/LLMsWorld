# libraries
import requests
import pandas as pd
from datetime import datetime
from openai import OpenAI
from bs4 import BeautifulSoup
from xhtml2pdf import pisa


client = OpenAI(
    api_key="your_open_ai_key"
)

# inputs
player_name = 'Francisco Conceição'
url = 'https://fbref.com/en/players/5ef3d210/Francisco-Conceicao'

attrs_percentile_stats = 'scout_summary_AM' # you need to change this for MF or DF,FW depending on the player position
attrs_sim_players = 'similar_AM' # also here

# percentile data
df = pd.read_html(
    url,
    attrs={'id': attrs_percentile_stats}
)[0]

# similar players names
df1 = pd.read_html(
    url,
    attrs={'id': attrs_sim_players}
)[0]

df1['Player_Club'] = df1['Player'] + ' (' + df1['Squad'] + ')'

sim_players = list(df1['Player_Club'][:6])
# print(sim_players)

# beautifulsoup initialization
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# player info extraction
position = soup.select_one('p:-soup-contains("Position")').text.split(':')[-2].split(' ')[0].strip()
birthday = soup.select_one('span[id="necro-birth"]').text.strip()

# there are some players without height in fbref description, in these cases comment this line
height = soup.select('#meta > div > p:nth-child(3) > span:nth-child(1)')[0].text.split('<span>')[0]

weight = soup.select('#meta > div > p:nth-child(3) > span:nth-child(2)')[0].text
foot = soup.select_one('p:-soup-contains("Footed")').text.split('Footed')[1].split(': ')[1]

age = (datetime.now() - datetime.strptime(birthday, '%B %d, %Y')).days // 365
team = soup.select_one('p:-soup-contains("Club")').text.split(':')[-1].strip()

media_item_div = soup.find('div', {'class': 'media-item'})
img_tag = media_item_div.find('img') if media_item_div else None

player_image_url = img_tag['src'] if img_tag else 'image URL default not found'

df = df.dropna(subset='Statistic')

df.head()

prompt = f"""
I need you to create a scouting report on {player_name}. Can you provide me with a summary of their strengths and weaknesses?

Here is the data I have on him:

Player: {player_name}
Height: {height}
Weight: {weight}
Position: {position}
Age: {age}
Team: {team}

List of similar players to {player_name} and respective clubs.
{df1.to_markdown()}

{df.to_markdown()}

Return the scouting report in the following HTML. Return just the code:


<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Report for {player_name}</title>
</head>
<body>
  <div style="position: relative; padding: 30px; display: flex; align-items: center;">
    <div style="flex: 0 0 auto;">
      <img src="{player_image_url}" alt=" {player_name} headshot">
    </div>
    <div style="margin-left: 20px;">
      <h1 style="color: darkblue; font-size: 28px;">Report for {player_name}</h1>
      <p>
        <span style="font-weight: bold;">Player:</span> {player_name}<br>
        <span style="font-weight: bold;">Height:</span> {height}<br>
        <span style="font-weight: bold;">Weight:</span> {weight}<br>
        <span style="font-weight: bold;">Position:</span> {position}<br>
        <span style="font-weight: bold;">Age:</span> {age}<br>
        <span style="font-weight: bold;">Team:</span> {team}
      </p>
    </div>
    <div style="flex: 1;"></div>
  </div>
  <div style="padding: 0 30px;">
    <h1 style="color: darkblue; text-align: center;">Summary</h1>
    <p>
      <a brief summary of the player's overall performance and if he would be beneficial to the team>
    </p>
    <h1 style="color: darkblue; text-align: left;">Strengths</h1>
    <ul>
      <li><i>a list of 1 to 3 strengths</i></li>
    </ul>
    <h1 style="color: darkblue; text-align: left;">Weaknesses</h1>
    <ul>
      <li><i>a list of 1 to 3 weaknesses</i></li>
    </ul>
    <h1 style="color: darkblue; text-align: left;">Potential</h1>
    <p>
      < assessment of the player's potential for growth >
    </p>
    <h1 style="color: darkblue; text-align: center;">Similar players</h1>
    <p> 
        < mention the similar players to {player_name}, mentioning the profile of the players associated >
    </p>
    <div style="text-align: center; margin-top: 50px;">
      <img src="https://raw.githubusercontent.com/ricardoandreom/Data/main/Images/Personal%20Logos/Half%20Space%20Preto.png" alt="Logo" style="width: 200px;">
    </div>
  </div>
</body>
</html>

"""

print(prompt)

# llm response to the prompt
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[
        {"role": "system", "content": "You are a professional football (soccer) scout."},
        {"role": "user", "content": prompt},
    ],
)

# llm response with html format ready to convert to pdf
html = response.choices[0].message.content

# path and name to save the report
output_pdf = "C:/Users/Admin/Desktop/AI report generator/reports/" + player_name + "_scouting_report.pdf"

print(html)

def convert_html_to_pdf(source_html, output_filename):
    result_file = open(output_filename, "w+b")
    pisa_status = pisa.CreatePDF(source_html, dest=result_file)
    result_file.close()
    return pisa_status.err


# Generate report
convert_html_to_pdf(html, output_pdf)
