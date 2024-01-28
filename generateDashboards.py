# Input login details from user
email = input("Please enter your email. ")
password = input("Now please enter your password. ")
with open('Scripts\login_info.txt', 'w') as f:
    f.write('Email: ' + email + '\n')
    f.write('Password: ' + password)

# Run scripts
exec(open('Scripts/generateTotalStandings.py').read())
exec(open('Scripts/generateMyTeamInfo.py').read())
exec(open('Scripts/generateBestPlayersGrowth.py').read())
exec(open('Scripts/generateAvailableMarket.py').read())
exec(open('Scripts/generateDash.py').read())
