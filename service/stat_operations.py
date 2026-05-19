import matplotlib.pyplot as plt
import pandas as pd
import datetime
from typing import Literal
from aiogram.types import FSInputFile
from service.user import User


'''
Group
==============
1. Which question is most often answered incorrectly
2. Correct/incorrect answers by day (week)
'''

def get_day_stat(user: User, user_stat: str) -> FSInputFile | bool:
    pass
    # '''
    # This function is based on a link (very helpful):
    # https://towardsdatascience.com/100-stacked-charts-in-python-6ca3e1962d2b
    # '''
    # # Get data from Google Sheets and create a DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # Define the data type for the "Date" column
    # df['Date'] = pd.to_datetime(df['Date'], dayfirst = True)

    # # Keep only records with today's date
    # df = df[df['Date'].dt.date == pd.Timestamp.now().date()]

    # # If a specific user was passed as an argument,
    # # additionally filter the table by that user
    # if user_stat != 'all':
    #     df = df[df['Login'] == user_stat]

    # if df.empty:
    #     return False

    # # Keep only the 'Login' and 'Result' columns
    # df = df.loc[:,['Login', 'Result']]

    # # Some magic that I don't quite understand yet
    # cross_tab_prop = pd.crosstab(index=df['Login'],
    #                             columns=df['Result'],
    #                             normalize="index")

    # # Sort by number of correct answers
    # cross_tab_prop = cross_tab_prop.sort_values('Correct')

    # # Create the chart
    # cross_tab_prop.plot(kind = 'barh', stacked = True, figsize = [7, 5])

    # # Save the image, bbox_inches = 'tight' removes extra whitespace
    # plt.savefig('fig.png', bbox_inches = 'tight')

    # # Return the file object
    # file = FSInputFile('fig.png')
    # return file

def get_week_stat(user: User, user_stat: str) -> FSInputFile:
    pass
    # # Get data from Google Sheets and create a DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # Keep records from the last week
    # date = datetime.datetime.now() - datetime.timedelta(days = 7)
    # df = df[df['Date'].astype('datetime64[ns]') >= date]

    # # If a specific user was passed as an argument,
    # # additionally filter the table by that user
    # if user_stat != 'all':
    #     df = df[df['Login'] == user_stat]

    # if df.empty:
    #     return False

    # # Keep only the 'Date' and 'Result' columns
    # df = df.loc[:,['Date', 'Result']]

    # # Some magic that is becoming slightly clearer.
    # # Reset the index since we need to get a list later.
    # # Otherwise the question itself would be the index.
    # cross_tab_prop = pd.crosstab(index = df['Date'],
    #                             columns = df['Result'],
    #                             normalize = 'index')

    # # Sort by number of correct answers
    # cross_tab_prop = cross_tab_prop.sort_values('Date')

    # # Create the chart
    # cross_tab_prop.plot(kind = 'bar', stacked = True, figsize = [5, 5], xlabel = '')
    # plt.title('Correct answer dynamics over the last 7 days')

    # # Save the image, bbox_inches = 'tight' removes extra whitespace
    # plt.savefig('fig.png', bbox_inches = 'tight')

    # # Return the file object
    # file = FSInputFile('fig.png')
    # return file

def get_failed_questions(user: User, user_stat: str, days: int = 7, ) -> list:
    pass
    # # Get data from Google Sheets and create a DataFrame
    # stat_from_sheet = gsheet.get_users_stat(user)
    # df = pd.DataFrame(stat_from_sheet[1:], columns = stat_from_sheet[0])

    # # Keep records from the last week
    # date = datetime.datetime.now() - datetime.timedelta(days = days)
    # df = df[df['Date'].astype('datetime64[ns]') >= date]

    # # If a specific user was passed as an argument,
    # # additionally filter the table by that user
    # if user_stat != 'all':
    #     df = df[df['Login'] == user_stat]

    # if df.empty:
    #     return False

    # # Select only questions with incorrect answers
    # df = df[df['Result'] == 'Incorrect']

    # # Keep only the 'Login' and 'Result' columns
    # df = df.loc[:,['Question (text)', 'Result']]

    # # Some magic that is becoming a bit clearer.
    # # Reset the index since we need to get a list later.
    # # Otherwise the question itself would be the index.
    # cross_tab_prop = pd.crosstab(index = df['Question (text)'],
    #                          columns = df['Result']).reset_index()

    # # Sort by number of incorrect answers from highest to lowest
    # cross_tab_prop = cross_tab_prop.sort_values('Incorrect', ascending = False)

    # # Convert to a list and return
    # return cross_tab_prop.head().values.tolist()
