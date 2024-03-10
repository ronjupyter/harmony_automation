# ../nbs/00_core.ipynb

# %% auto 0
__all__ = ['PKG_DIR', 'CFG', 'serv', 'driver', 'fp', 'return_yaml_data', 'search_for_xpath_elem', 'return_data', 'login',
           'search_ticket_num', 'view_log', 'click_edit_log', 'edit_res', 'submit_res', 'reassign_log',
           'test_page_source_ok', 'extract_notes_from_page_source', 'scrape_with_bsoup', 'scraped_notes_to_df',
           'load_edited_details']

# %% ../nbs/00_core.ipynb 2
import base64
import os
import sys
import time
from datetime import datetime

import gspread
import pandas as pd
import pkg_resources
import pytest
import yaml
from bs4 import BeautifulSoup
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from icecream import ic
from loguru import logger as lg
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

PKG_DIR = pkg_resources.resource_filename(__name__, ".")

# %% ../nbs/00_core.ipynb 3
ic.configureOutput(outputFunction=lambda x: lg.info(x), prefix="")
try:
    lg.remove(0)
except:
    pass
lg.add("harmony_automation.log", format="{time} | {level} | {message}", level=5)

# %% ../nbs/00_core.ipynb 5
def fp(relative_fp: str, base_dir: str = PKG_DIR) -> str:
    """If imported, pkg dir == `pkg/pkg` and relative paths are the same as in notebook env. Need to adjust when running `nbdev_docs`.

    Parameters
    ----------
    relative_fp : str
        str - eg. "../dir/file.txt"
    base_dir : str, optional
        str

    Returns
    -------
    str
        str
    """
    docs_mode = not os.path.exists(os.path.join(base_dir, relative_fp))

    if docs_mode:
        relative_fp = relative_fp.replace("..", ".", 1)

    return os.path.join(base_dir, relative_fp)

# %% ../nbs/00_core.ipynb 6
def return_yaml_data(file_path: str) -> dict:
    """...

    Parameters
    ----------
    file_path : str
        str

    Returns
    -------
    dict
        dict
    """
    with open(file_path, "r") as f:
        data = yaml.safe_load(f.read())

    return data

# %% ../nbs/00_core.ipynb 7
CFG = return_yaml_data(fp("../cfg/config.yaml"))
serv = Service(executable_path=CFG["chromedriver"])
driver = webdriver.Chrome(service=serv)

# %% ../nbs/00_core.ipynb 9
# * FINAL
def search_for_xpath_elem(xpath_str: str, time_limit: int = 30) -> list:
    """While len of search list is 0, keep searching. If exceeds time limit (seconds, approximate),  returns empty list.

    Parameters
    ----------
    xpath_str : str
        str
    time_limit : int, optional
        int

    Returns
    -------
    list
        List[WebElement]
    """
    ctr = 0
    t_search = driver.find_elements(By.XPATH, xpath_str)

    while (len(t_search) == 0) and (ctr < time_limit):
        time.sleep(1)
        ctr += 1
        t_search = driver.find_elements(By.XPATH, xpath_str)

    if len(t_search) > 0:
        return t_search
    else:
        return []

# %% ../nbs/00_core.ipynb 11
# * FINAL
def return_data() -> pd.DataFrame:
    """Load and clean one of the output files created from the update script - `for_log_tracker_...xlsx`

    Returns
    -------
    pd.DataFrame
        pd.DataFrame
    """
    latest = sorted(os.listdir(fp("../dat")))[-1]
    print(latest)

    df = pd.read_excel(fp(f"../dat/{latest}"))
    df = df[["ticket_num", "death_update"]].copy()
    df.columns = ["ticket_num", "log_action"]

    return df

# %% ../nbs/00_core.ipynb 13
# * FINAL
def login() -> None:
    """Log in to Harmony"""
    driver.get(CFG["url"])

    t_search = search_for_xpath_elem(CFG.get("username_xpath"))
    t_search[0].send_keys(CFG["user"])

    t_search = search_for_xpath_elem(CFG.get("password_xpath"))
    t_search[0].send_keys(CFG["pass"])
    time.sleep(1)
    t_search[0].send_keys(Keys.RETURN)


def search_ticket_num(ticket_num: str) -> None:
    """Go to ticket number search page and search for `ticket_num`

    Parameters
    ----------
    ticket_num : str
        str
    """
    # click search by ticket number
    time.sleep(1)
    t_search = search_for_xpath_elem(CFG.get("log_search_xpath"))
    time.sleep(0.5)
    t_search[0].click()

    # refresh
    t_search = search_for_xpath_elem(CFG.get("refresh_btn_xpath"))
    time.sleep(1)
    t_search[0].click()

    # input ticket number
    t_search = search_for_xpath_elem(CFG.get("tkt_num_input_xpath"))
    time.sleep(1)
    t_search[0].send_keys(str(ticket_num))

    # click search
    t_search = search_for_xpath_elem(CFG.get("tkt_num_button_xpath"))
    time.sleep(1)
    t_search[0].click()


def view_log() -> None:
    """Clicks `view log` of search result"""
    # there should only be one result
    t_search = search_for_xpath_elem(CFG.get("result_actions_xpath"))
    time.sleep(1)
    t_search[0].click()

    # view log
    t_search = search_for_xpath_elem(CFG.get("view_log_btn_xpath"))
    time.sleep(1)
    t_search[0].click()


def click_edit_log() -> None:
    """Clicks `edit` button"""
    t_search = search_for_xpath_elem(CFG.get("log_edit_btn_xpath"))
    time.sleep(1)
    t_search[0].click()


def edit_res(comment="done") -> None:
    """Add `comment` to resolution input box

    Parameters
    ----------
    comment : str, optional
        str
    """
    # xpath for resolution input differs by log type
    xpath_list = CFG.get("resolution_input_xpath_list")
    t_search = []
    while len(t_search) == 0:
        for xpath_str in xpath_list:
            t_search = driver.find_elements(By.XPATH, xpath_str)
            try:
                t_search[0].send_keys(comment)
            except:
                pass
            else:
                t_search = [0]
                break


def submit_res() -> None:
    """Clicks `submit`"""
    # xpath for submit button differs by log type
    xpath_list = CFG.get("submit_btn_xpath_list")
    t_search = []
    while len(t_search) == 0:
        for xpath_str in xpath_list:
            t_search = driver.find_elements(By.XPATH, xpath_str)
            try:
                t_search[0].click()
            except:
                pass
            else:
                t_search = [0]
                break


def reassign_log(note: str) -> None:
    """Actions to execute on ticket number search results page

    Parameters
    ----------
    note : str
        str
    """
    # there should only be one result
    t_search = search_for_xpath_elem(CFG.get("result_actions_xpath"))
    time.sleep(0.5)
    t_search[0].click()

    # click re-assign
    t_search = search_for_xpath_elem(CFG.get("reassign_btn_xpath"))
    time.sleep(0.5)
    t_search[0].click()

    # enter name
    t_search = search_for_xpath_elem(CFG.get("search_user_xpath"))
    time.sleep(0.5)
    t_search[0].send_keys(CFG.get("colleague"))
    time.sleep(0.3)
    t_search[0].send_keys(Keys.RETURN)

    # click assign button
    t_search = search_for_xpath_elem(CFG.get("assign_btn_xpath"))
    time.sleep(0.3)
    t_search[0].click()

    # enter reason
    t_search = search_for_xpath_elem(CFG.get("reason_input_xpath"))
    time.sleep(0.5)
    t_search[0].send_keys(note)

    # submit reason
    time.sleep(1.5)
    submit_reason_xpath = CFG.get("submit_reason_xpath")
    t_search = driver.find_elements(By.XPATH, submit_reason_xpath)
    t_search[0].click()

# %% ../nbs/00_core.ipynb 15
# * FINAL
def test_page_source_ok(page_source: str) -> bool:
    """Checks if the right page is loaded

    Parameters
    ----------
    page_source : str
        str

    Returns
    -------
    bool
        bool
    """
    soup = BeautifulSoup(page_source, "lxml")
    notes = soup.find_all("p", class_="prewrapped-text")
    return len(notes) > 1


def extract_notes_from_page_source(page_source: str) -> str:
    """Extracts and cleans notes/comments from log page source

    Parameters
    ----------
    page_source : str
        str

    Returns
    -------
    str
        str
    """
    soup = BeautifulSoup(page_source, "lxml")
    notes = soup.find_all("p", class_="prewrapped-text")
    notes_lst = [n.get_text().replace("\n", "  ") for n in notes]
    return "\n\n".join([notes_lst[0]] + notes_lst[1:][::-1])


def scrape_with_bsoup(ticket_str: str) -> str:
    """Opens log, extracts/cleans notes/comments, format and return

    Parameters
    ----------
    ticket_str : str
        str - "<ticket_num> <employee_id> - "

    Returns
    -------
    str
        str - "<employee_id> - <notes/comments>  <url>"
    """
    note_start = ticket_str.split(" ", 1)[-1]
    ticket_num = ticket_str.split(" ", 1)[0]
    search_ticket_num(ticket_num)
    view_log()
    harmony_url = ""
    while "cmLogViewPage" not in harmony_url:
        time.sleep(0.1)
        harmony_url = driver.current_url
        page_source = driver.page_source

    test_page_source = test_page_source_ok(page_source)
    while test_page_source == False:
        time.sleep(0.1)
        page_source = driver.page_source
        test_page_source = test_page_source_ok(page_source)

    result = extract_notes_from_page_source(page_source)
    return f"{note_start}\n\n{result}\n{harmony_url}"


def scraped_notes_to_df(input_ticket_strs: list[str]) -> pd.DataFrame:
    """For list of ticket numbers, returns formatted details and add to dataframe - see `scrape_with_bsoup`

    Parameters
    ----------
    input_ticket_strs : list[str]
        list[str]

    Returns
    -------
    pd.DataFrame
        pd.DataFrame
    """
    result_df = pd.DataFrame(columns=["ticket_str", "details"])

    for ticket_str in input_ticket_strs:
        if "updated" in ticket_str:
            notes = "updated"
        else:
            notes = scrape_with_bsoup(ticket_str=ticket_str)
        result_df.loc[len(result_df)] = list((ticket_str, notes))

    return result_df


def load_edited_details(_=None) -> list[str]:
    """Result of `scraped_notes_to_df` gets exported to excel and manual edits are made, if needed. This function loads the edited file and cleans up the details column to add back to the log tracker.

    Parameters
    ----------
    _ : ...
        disregard

    Returns
    -------
    list[str]
        list[str]
    """

    output_file = sorted([x for x in os.listdir() if x.lower().endswith(".xlsx")])[-1]
    df = pd.read_excel(output_file)

    details_list_cleaned = []
    details_list = df["details"].tolist()
    for l in details_list:
        t_list = l.split("\n")
        clean_note = "\n".join([x for x in t_list if x.strip() != "-"])
        details_list_cleaned.append(clean_note)

    return [
        x.replace("\n", "").strip().replace("https:", "   https:")
        for x in details_list_cleaned
    ]
