from calendar import day_name
import struct
from selenium import webdriver  
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.common.by import By
from datetime import timedelta
from math import floor
from datetime import datetime as dt
from time import gmtime, sleep, strftime
import json

jira_user = "ivan"
jira_pass = "ivan"

nl_protocol_page = "http://192.168.1.3:8080/browse/EBA-11877"
jiraPage = "http://192.168.1.3:8080/secure/Dashboard.jspa"
user_XPATH = "/html/body/div[1]/section/dashboard/div[1]/div/div[5]/div/div[2]/div/div/form/div[1]/input"
pass_XPATH = "/html/body/div[1]/section/dashboard/div[1]/div/div[5]/div/div[2]/div/div/form/div[2]/input"
login_button = "/html/body/div[1]/section/dashboard/div[1]/div/div[5]/div/div[2]/div/div/form/div[4]/div/input"
time_spent = "/html/body/div[10]/div[2]/form/div[1]/fieldset/div[1]/input"
date_started = "/html/body/div[10]/div[2]/form/div[1]/fieldset/div[2]/input"
work_description = "/html/body/div[10]/div[2]/form/div[1]/fieldset/div[4]/textarea"
log_work = "/html/body/div[10]/div[2]/form/div[2]/div/input"


class ticket_struct:
    def __init__(self,ticket_name,ticket_page,ticket_message,ticket_H,ticket_M):
        self.ticket_name = ticket_name  
        self.ticket_page = ticket_page  
        self.ticket_H = ticket_H
        self.ticket_M = ticket_M
        self.ticket_time = str(ticket_H) + "h " + str(ticket_M) + "m"
        self.ticket_message = ticket_message

class day_struct:
    def __init__(self, date, message):
        date = date.split("-")
        date[0] = date[0][2:]
        date = "-".join(date)
        aux_dateTime = dt.strptime(date, "%y-%m-%d")
        aux_dateTime = aux_dateTime.strftime("%d/%b/%y") + " 08:00 PM"
        if aux_dateTime[0] == "0":
            aux_dateTime = aux_dateTime[1:]
        self.date = aux_dateTime
        self.message = str(message)
        self.tickets = {}

def get_ticket_page(ticket_id):
    #open the projects_key.json file
    f = open('projects_key.json')
    data = json.load(f)
    f.close()
    keys = data['keys']
    #get the ticket page
    if ticket_id in keys:
        ticket_page = keys[ticket_id]
    else:
        ticket_page = "Not found"
        for cont in range(1,100):
            print("page not found please fix the ticket id"+ ":" + ticket_id )
    return ticket_page

def read_time_file(file_path):
    #open hours file
    f = open(file_path, "r")
    hours = f.readlines()
    f.close()
    string = "".join(hours)
    return string 

def make_list_of_days (string): #each node contains the day and a lis of tickets
    string = string.replace("\t", "")
    string_list = string.split("\n")
    day_struct_list = []
    day = ""
    day_string = ""
    for string in string_list:
        if("2022-" in string):
            if day != "":
                day_struct_list.append(day_struct(day, day_string))
            day = string
            day_string = ""
        else:
            day_string = day_string + string + " \n"
    day_struct_list.append(day_struct(day, day_string))
    return day_struct_list

def calculate_time(ticket_H , ticket_M, string_list):
    if ticket_H == "":
        ticket_H = "00"
        ticket_M = "00"
    ticket_H = int(ticket_H)
    ticket_M = int(ticket_M)
    
    hours1 = string_list[0].split(":")[0]
    minutes1 = string_list[0].split(":")[1]
    time1 = timedelta(hours=int(hours1), minutes=int(minutes1))
    
    #add current time to the time2 (extend hours for stuff already worked on previus line of the file)
    hours2 = int(string_list[2].split(":")[0]) + int(ticket_H)
    minutes2 = int(string_list[2].split(":")[1]) + int(ticket_M)
    time2 = timedelta(hours=int(hours2), minutes=int(minutes2))
    
    aux_time = time2 - time1
    ticket_H = floor(aux_time.total_seconds()/3600)
    ticket_M = floor(aux_time.total_seconds()/60 - ticket_H*60)
    
    return  ticket_H , ticket_M

def make_list_of_tickets(day_struct_list):
    for day in day_struct_list:
        message = day.message.split("\n")
        message = list(filter(None, message))

        for line in message:
            
            aux_line = line.split(" ")
            line_id = aux_line[3]
            line_message = " ".join(aux_line[0:3]) + " " + " ".join(aux_line[4:])
            #if ticket already exists in dict get the ticket
            if line_id in day.tickets:
                ticket = day.tickets[line_id]
                ticket.ticket_H ,ticket.ticket_M = calculate_time(ticket.ticket_H ,ticket.ticket_M, aux_line)
                ticket.ticket_message = ticket.ticket_message + "\n" + line_message
                ticket.ticket_time = str(ticket.ticket_H) + "h " + str(ticket.ticket_M) + "m"
            else:
                ticket_H ,ticket_M = calculate_time("" ,"", aux_line)
                ticket_page = get_ticket_page(line_id)
                ticket = ticket_struct(line_id, ticket_page, line_message ,ticket_H, ticket_M)
                day.tickets[line_id] = ticket    
            print("pause")
    return day_struct_list

def upload_to_jira(day_struct_list):
    browser = webdriver.Chrome("driver\\chromedriver.exe")  
    browser.maximize_window()  
    browser.get(jiraPage)
    sleep(3)
    browser.find_element_by_xpath(user_XPATH).send_keys(jira_user)
    browser.find_element_by_xpath(pass_XPATH).send_keys(jira_pass)
    sleep(1)
    browser.find_element_by_xpath(login_button).click()
    sleep(1)

    list_of_ticket_pages_to_ignore = ["Not found"]
    for day in day_struct_list:
        for ticket in day.tickets:
            ticket = day.tickets[ticket]
            ticket_message = ticket.ticket_message
            ticket_page = ticket.ticket_page
            ticket_time = ticket.ticket_time
            ticket_date = day.date
            if ticket_page not in list_of_ticket_pages_to_ignore:
                print("pause")
                browser.get(ticket_page)
                sleep(3)
                browser.find_element_by_xpath("/html/body/div[1]/section/div[2]/div/div/div/div/div[2]/div/header/div/div/div/div/div/div[1]/div[3]/a[2]").click()
                browser.find_element_by_xpath("/html/body/aui-dropdown-menu/div/aui-section[1]/div/aui-item-link").click()
                sleep(1)
                browser.find_element_by_xpath(time_spent).send_keys(ticket_time)
                browser.find_element_by_xpath(date_started).clear()
                sleep(1)
                browser.find_element_by_xpath(date_started).send_keys(ticket_date)
                browser.find_element_by_xpath(work_description).send_keys(ticket_message)
                browser.find_element_by_xpath(log_work).click()
                sleep(3)
def upload_tickets(day_struct_list):
    upload_to_jira(day_struct_list)

def main_program(aux_string):
    #1 read the file 
    string = read_time_file("hours.txt")
    #2 make a list of days
    day_struct_list = make_list_of_days(string)
    #3 create the tickets
    day_struct_list = make_list_of_tickets(day_struct_list)
    #upload the tickets
    upload_tickets(day_struct_list)    

main_program("aux")
print("pause")