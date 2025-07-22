import holidays.countries
import pandas as pd

def custom_holiday():
    custom_holidays = holidays.Russia()
    custom_holidays.append({"2025-03-01":"may pr","2025-03-02":"may pr","2025-03-08":"may pr","2025-03-09":"may pr","2024-11-04":"may pr"})
    return custom_holidays

rus_holidays = custom_holiday()

def deadline_calc(project,start_date,end_date):
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        mes,push = mes_and_push(start_date)
        master_task = start_date
        local_task = add_workdays(start_date,-2)
        text_task = add_workdays(local_task,-1)
        design_task_start = add_workdays(start_date,-3)
        design_task = add_workdays(design_task_start,-2)
        setting_task = design_task_start
        email_task = add_workdays(start_date,-1)
        content_task = add_workdays(start_date,-1)
        news_placement = check_day(start_date,-1)
        news_deadline = add_workdays(news_placement,-2)
        email_deadline = add_workdays(start_date,-2)
        banner_placement = check_day(start_date,-1)
        banner_deadline = add_workdays(banner_placement,-1)
        page_placement = add_workdays(start_date,-1)
        page_deadline = add_workdays(page_placement,-1)
        msngr_deadline = mes
        push_deadline = push
        if end_date.hour > 14:
            print("Конец",end_date)
            end_news_placement = add_workdays(end_date,1)
            print('Дата',end_news_placement)
            end_news_deadline = add_workdays(end_news_placement,-1)
        else:
            end_news_placement = check_day(end_date,1)
            end_news_deadline  = add_workdays(end_news_placement,-1)   
        text = f"""
                Задача и сроки \n
                Мастер-таск: {master_task.strftime('%d-%m-%Y')}\n
                Задача на тексты: {text_task.strftime('%d-%m-%Y')}\n
                Задача на локализацию: {local_task.strftime('%d-%m-%Y')}\n
                Задача на дизайн(дата старта): {design_task_start.strftime('%d-%m-%Y')}\n
                Задача на дизайн(срок исполнения): {design_task.strftime('%d-%m-%Y')}\n
                Задача на настройку: {setting_task.strftime('%d-%m-%Y')}\n
                Задача на отправку письма: {email_task.strftime('%d-%m-%Y')}\n
                Задача на контент: {content_task.strftime('%d-%m-%Y')}\n
                Размещение и дедлайны \n
                Новость(Размещение): {news_placement.strftime('%d-%m-%Y')}\n
                Новость(Дедлайн): {news_deadline.strftime('%d-%m-%Y')}\n
                Письмо(Дедлайн): {email_deadline.strftime('%d-%m-%Y')}\n
                Баннер(Размещение): {banner_placement.strftime('%d-%m-%Y')}\n
                Баннер(Дедлайн): {banner_deadline.strftime('%d-%m-%Y')}\n
                Страница турнира(Размещение): {page_placement.strftime('%d-%m-%Y')}\n
                Страница турнира(Дедлайн): {page_deadline.strftime('%d-%m-%Y')}\n
                Мессенджер(Дедлайн): {msngr_deadline.strftime('%d-%m-%Y')}\n
                Пуш(Дедлайн): {push_deadline.strftime('%d-%m-%Y')}\n
                Новость на завершение(Размещение): {end_news_placement.strftime('%d-%m-%Y')}\n
                Новость на завершение(Дедлайн): {end_news_deadline.strftime('%d-%m-%Y')}\n"""

        return text 
        
        
def deadline_calc_dict(project,start_date,end_date):
        start_date = pd.Timestamp(start_date)
        end_date = pd.Timestamp(end_date)
        mes,push = mes_and_push(start_date)
        mes_pl,push_pl = mes_and_push_placement(start_date)
        master_task = start_date
        local_task = add_workdays(start_date,-2)
        text_task = add_workdays(local_task,-1)
        msngr_placement_deadline = add_workdays(mes_pl,-1)
        design_task_start = add_workdays(start_date,-3)
        design_task = add_workdays(design_task_start,-2)
        setting_task = design_task_start
        msngr_placement = mes_pl
        msngr_placement_deadline = add_workdays(start_date,-1)
        push_placement = push_pl
        email_task = add_workdays(start_date,-1)
        content_task = add_workdays(start_date,-1)
        smm_date = add_workdays(start_date,-1)
        news_placement = check_day(start_date,-1)
        news_deadline = add_workdays(news_placement,-2)
        email_deadline = add_workdays(start_date,-2)
        banner_placement = check_day(start_date,-1)
        banner_deadline = add_workdays(banner_placement,-1)
        page_placement = add_workdays(start_date,-1)
        page_deadline = add_workdays(page_placement,-1)
        page_deadline_title = page_deadline
        msngr_deadline = mes
        push_deadline = push
        if end_date.hour > 14:
            print("Конец",end_date)
            end_news_placement = add_workdays(end_date,1)
            print('Дата',end_news_placement)
            end_news_deadline = add_workdays(end_news_placement,-1)
        else:
            end_news_placement = check_day(end_date,1)
            end_news_deadline  = add_workdays(end_news_placement,-1)   
        dict_result ={
        "master_task" : master_task.strftime('%Y-%m-%d'),
        "master_task_d" : master_task.strftime('%d/%m'),
        "local_task" : local_task.strftime('%Y-%m-%d'),
        "text_task" : text_task.strftime('%Y-%m-%d'),
        "local_task_d" : local_task.strftime('%d/%m'),
        "text_task_d" : text_task.strftime('%d-%m-%Y'),
        "design_task_start" : design_task_start.strftime('%d-%m-%Y'),
        "design_task" : design_task.strftime('%Y-%m-%d'),
        "design_task_d" : design_task.strftime('%d-%m-%Y'),
        "setting_task" : setting_task.strftime('%Y-%m-%d'),
        "setting_task_d" : setting_task.strftime('%d/%m'),
        "email_task" : email_task.strftime('%Y-%m-%d'),
        "content_task" : content_task.strftime('%d-%m-%Y'),
        "news_placement" : news_placement.strftime('%d-%m-%Y'),
        "news_deadline" : news_deadline.strftime('%d-%m-%Y'),
        "banner_placement" : banner_placement.strftime('%d-%m-%Y'),
        "banner_deadline" : banner_deadline.strftime('%d-%m-%Y'),
        "page_placement" : page_placement.strftime('%Y-%m-%d'),
        "page_placement_d" : page_placement.strftime('%d-%m-%Y'),
        "page_placement_s" : page_placement.strftime('%d/%m'),
        "page_deadline" : page_deadline.strftime('%d-%m-%Y'),
        'page_deadline_title':page_deadline_title.strftime('%d/%m'),
        "msngr_deadline" : msngr_deadline.strftime('%d-%m-%Y'),
        "push_deadline" : push_deadline.strftime('%d-%m-%Y'),
        "end_news_placement" : end_news_placement.strftime('%d-%m-%Y'),
        "end_news_deadline" : end_news_deadline.strftime('%d-%m-%Y'),
        'email_deadline': email_deadline.strftime('%d-%m-%Y'),
        'smm_date': smm_date.strftime('%d-%m-%Y'),
        'msngr_placement': msngr_placement.strftime('%d-%m-%Y'),
        'push_placement': push_placement.strftime('%d-%m-%Y'),
        "msngr_placement_deadline" : msngr_placement_deadline.strftime('%Y-%m-%d')
    }
        return dict_result
def check_day(start_date,days):
    
    step = 1 if days >= 0 else -1
    remaining_days = abs(days)
    while remaining_days > 0:
        if start_date.weekday() < 5 and start_date not in rus_holidays:
            remaining_days -= 1
        else:
            start_date += pd.Timedelta(days=step)
    return start_date
        
def add_workdays(start_date, days):
    current_date = start_date
    step = 1 if days >= 0 else -1
    remaining_days = abs(days)
    
    while remaining_days > 0:
        current_date += pd.Timedelta(days=step)
        if current_date.weekday() < 5 and current_date not in rus_holidays:
            remaining_days -= 1
        
    return current_date


def mes_and_push(start_date):
    mess_date = start_date + pd.Timedelta(days=1)
    push_date = start_date + pd.Timedelta(days=2)
    print(mess_date.weekday(),push_date.weekday())
    if mess_date.weekday() in [5,6,7] and push_date.weekday() in [5,6,7]:
        while mess_date.weekday() != 3:
            mess_date = mess_date + pd.Timedelta(days= -1)
        while push_date.weekday() != 3:
            push_date = push_date + pd.Timedelta(days= -1)  
        return mess_date,push_date
    else:
        mess_date = add_workdays(mess_date,-1)
        push_date = add_workdays(push_date,-1)
        return mess_date,push_date


def mes_and_push_placement(start_date):
    mess_date = start_date + pd.Timedelta(days=1)
    push_date = start_date + pd.Timedelta(days=2)
    return mess_date,push_date


def test():
    start_date = pd.Timestamp('03-12-2024')
    print(start_date)


