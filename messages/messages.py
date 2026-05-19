CONGRATS = ['💪 Great job! Keep it up!',
            '🔪 Wild, bold, sharp as a bullet!',
            '🤙 Nailed it!',
            '🔥 On fire!',
            '💡 Magnificent!',
            '🥸 You\'re a pro!',
            '🎯 Bullseye!',
            '👍 Well done!',
            '💰 I think you can ask for a raise!',
            '🥇 You\'re a champion!',
            '👏 Brilliant!',
            '💯 Incredibly accurate answer!',
            '🍹 Wonderful!',
            '👊 Top notch!',
            '💎 Diamond performance!',
            '🍾 Hooray!',
            '🚀 Simply stellar!',
            '🌟 Star result!',
            '🎉 Masterful!',
            '🏆 Unmatched!',
            '🎇 Impressive!',
            '🌈 Bright and beautiful!',
            '🌺 Great work!',
            '🔝 You\'re at the top!',
            '💥 Mind-blowing!',
            '💫 You\'re a star!',
            '🤩 Brilliant!',
            '🍀 Luck is on your side!',
            '🦄 Magical!'
            ]

WRONG = ['You\'ll get it next time!',
         'Hmm.. almost...)',
         'Don\'t give up!',
         'Just focus!',
         'Maybe you should revisit the questions after a cup of ☕️?',
         'Aww... want to try again?',
         'That\'s not quite right(',
         'So close, but not quite(']

READY = ['Ready!',
         'Bring it on!',
         '🚀 Let\'s go!',
         'Can\'t wait!',
         'Let\'s fly!',
         'Onwards to victory!',
         'Faster, faster!',
         'I\'ll ace it 💯!',
         'Let\'s go all in!',
         'Onwards to new achievements!',
         'What have you got for me?',
         'These easy questions again?',
         'Let\'s sort this out',
         'I\'m something of an expert myself',
         'Let\'s see',
         'I\'ve been waiting!',
         'In anticipation!']


         # 'Easy as pie!',   
         # ,
         # ,
         # 'Like taking candy from a baby!',
         # ,
         # ,
         # ,
         # ',
         # 'Bet I can answer without even looking?'
         

MESSAGES = {'welcome_message' : "Hello! ✋\n\n"
                                    "🤖 Booosted Quick Quiz Bot is happy to welcome you!\n\n"
                                    "📌 I was created for one purpose – to ask you questions at a specific time, so you never forget important information.\n\n"
                                    "🎮 The quiz will start automatically if you have already been added to a quiz. Questions are sent every day between 10 and 11 AM\n\n\n"
                                    "Good luck!",

            'help_message' : "Here will be text about commands and how to use the bot",

            'add_question_help_message' : "Hello! Here will be help text for adding a new question.",
            'create_new_table_instruction': "Instructions:\n"
                                            "All questions for the bot are taken from a spreadsheet. A user can create their own spreadsheet or be invited to someone else's.\n\n"
                                            "1️⃣ Follow the link https://docs.google.com/spreadsheets/d/1D6DCi2yb9gshzj7Hf6aRvgfL0EDM65H9XUODKl_fSME/copy\n\n"
                                            "2️⃣ Google will offer to copy the sample spreadsheet. Save it to your Google Drive in any convenient location.\n\n"
                                            "3️⃣ Write questions, specify correct and incorrect answers. If desired, in the *users tab specify who else will use the spreadsheet.\n\n"
                                            "4️⃣ Be sure to grant full access to the service account (service@quickquizbot.iam.gserviceaccount.com) or to anyone with the link."
                                            "4️⃣ Send me the link to the created spreadsheet (copy it directly from the address bar as-is)\n\n"
                                            "5️⃣ Question delivery will be scheduled automatically, and the next day at 10 AM everyone listed in *users will receive them.\n\n"
                                            "A bit about the spreadsheet structure\n\n"
                                            "🍏 By default you have three tabs: Main, *stat and *users\n\n"
                                            "🍑 Main – this is the question list itself. It contains the question text, the correct answer and several incorrect ones. You can specify as many incorrect answers as you want.\n\n"
                                            "🍐 You can create additional tabs and name them as you wish. This allows you to group questions by topic. For example: corporate culture, accounting basics, sales process, etc.\n\n"
                                            "🍊 The *stat tab is designed to collect statistics: who answered which questions, when, what answer was given, and whether it was correct. Please do not change anything in this tab so the bot works correctly.\n\n"
                                            "🍋 The *users tab stores information about who receives questions, which ones and how many. To add a user, simply enter their login (without @) in the corresponding field. For convenience, you can also specify their full name (useful in the statistics tab). In the available lists field you can specify which tabs this user will receive questions from and how many. For example, if you need 10 questions from the Main tab and 5 from the Corporate Culture tab, write: Main: 10, Corporate Culture: 5\n\n"
                                            "🍌 All questions are sent in turn between 10 and 11 AM every working day"}


ALERTS = {'question_added' : "Great! We have added a new question!\n\n"}

CONFIRMATIONS = {'question_confirmed' : "Yes, that's correct",
                'question_not_confirmed' : "No, let's redo everything"}
