#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Revenant"
# __version__ = "0.1.0"
# __license__ = "MIT"


def main():
    ## Set Vars
    workingDir = '/home/jarvis/DatDownloader'
    datDownloadDir = '/DATs/downloads/'

    ## Determine latest zip file name
    from datetime import date
    today = date.today()
    YYYYMMDD_date = today.strftime('%Y-%m-%d')
    zipped_dats = 'No-Intro Love Pack (PC XML) (' + str(YYYYMMDD_date) + ').zip'

    ## Check for todays DATs
    from pathlib import Path

    if Path(workingDir + datDownloadDir + zipped_dats).is_file():
        print(zipped_dats + " exists and download will be skipped")
    else:
        print(zipped_dats + " does not exist and will be downloaded")
        ## Grab the latest DATs
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.firefox.options import Options

        options = Options()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.manager.showWhenStarting", False)
        options.set_preference("browser.download.dir", workingDir + datDownloadDir)
        options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

        driver = webdriver.Firefox(options=options)

        driver.get('https://datomatic.no-intro.org/index.php?page=download&op=daily&s=64')

        rb_parentchild_xml = driver.find_element(By.XPATH, '/html/body/div/section/article/div/form/input[2]')
        rb_parentchild_xml.click()

        cb_nongame = driver.find_element(By.XPATH, '/html/body/div/section/article/div/form/input[8]')
        cb_nongame.click()

        btn_request = driver.find_element(By.XPATH, '/html/body/div/section/article/div/form/input[9]')
        btn_request.click()

        btn_download = driver.find_element(By.XPATH, '/html/body/div/section/article/div/form/input')
        btn_download.click()

        driver.quit()    

    ## Unzip the dats
    import zipfile

    current_dats = 'DATs/Latest/'

    with zipfile.ZipFile(workingDir + datDownloadDir + zipped_dats, 'r') as zipObj:
        zipObj.extractall(current_dats)

    ## Create and update database
    import psycopg2
    import re
    from datetime import datetime

    try:
        conn = psycopg2.connect(database = "potato", user = "potato", password = "PotatoMan16!", host = "localhost", port = "5432")
    except:
        print("I am unable to connect to the database") 

    cur = conn.cursor()
    try:
        # Check if table exists
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tbl_current_dats');")
        result = cur.fetchone()

        if result[0] == False:
            # Create if missing
            print ("tbl_current_dats table not found. Creating...")
            cur.execute("""
                        CREATE TABLE tbl_current_dats (
                        cdat_id SERIAL PRIMARY KEY,
                        cdat_filename VARCHAR(255),
                        cdat_manufacturer varchar(50),
                        cdat_system VARCHAR(60),
                        cdat_timestamp timestamp,
                        cdat_group VARCHAR(30));
                    """)
        else:
            # Add latest dats to database
            with open(current_dats + 'index.txt', 'r') as file:
                for line in file:
                    # Remove new line character
                    line = line.rstrip('\n')
                    
                    #Reset vars
                    timestamp = ''
                    match_manufacturer = ''
                    match_system = ''
                    match_group = ''
                    match_hyphen = ''
                    group = ''

                    # Break down filename for variables
                    match_timestamp = re.search(r'\((\d{8}-\d{6})\)', line)

                    # Check if line contains a hypen
                    match_hyphen = re.search(r'.*-.*\(Parent-Clone\)', line)
                    if match_hyphen is None:
                        # Modify for hypenless lines
                        match_system = re.search(r'(.*?) \(Parent-Clone\)', line)

                        # Hard code for Bandai and Project EGG
                        match_manufacturer = re.match(r'(\w+)', line)
                        group = "No-Intro"
                    else:                    
                        match_group = re.search(r'(.+?) -', line)
                        # If line starts with group name
                        if match_group.group(1) in ("Source Code", "Non-Redump", "Unofficial", "Non-Game"):
                            match_manufacturer = re.search(r'.+? - (.+?) -', line)     
                            match_system = re.search(r'- .*? - (.*?) \(Parent-Clone\)', line)
                            group = match_group.group(1)     
                        else:
                            match_manufacturer = re.search(r'(.+?) -', line)
                            match_system = re.search(r'- (.*?) \(Parent-Clone\)', line)
                            group = "No-Intro"

                    if match_timestamp:
                        timestamp = datetime.strptime(match_timestamp.group(1), '%Y%m%d-%H%M%S').isoformat()
                    else:
                        timestamp = datetime.now().isoformat()  # Should this be blank?

                    if match_manufacturer:
                        manufacturer = match_manufacturer.group(1)
                        # Hardcode fix for Project EGG
                        if manufacturer == "Project":
                            manufacturer == "D4 Enterprise"
                    else:
                        manufacturer = "Unknown"

                    if match_system:
                        system = match_system.group(1)
                    else:
                        system = "Unknown"

                    # Insert current values into database
                    cur.execute("INSERT INTO tbl_current_dats (cdat_filename, cdat_timestamp, cdat_manufacturer, cdat_system, cdat_group) VALUES (%s, %s, %s, %s, %s);", (line, timestamp, manufacturer, system, group, ))
                    print("[Inserted] Row inserted for " + line + " dat.")        
    except Exception as e:
        print("I can't update the database!")
        print(f"Caught an exception: {e}")


    # TODO: Create the other tables required
    #       Populate them as well
    #       Add logic to determine if specific dats are to be kept/updated or skipped
    #       Add logic to compare the lastest with whats currently being used
    #       Move wanted dats to correct location
    #       Incorporate 1G1R somehow

    conn.commit() # <--- makes sure the change is shown in the database
    conn.close()
    cur.close()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()