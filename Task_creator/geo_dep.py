import json
from jira import JIRA
from jinja2 import Template
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from utils.data_info import manager_pr, lang_dict, geo_dep_task





class GeoDepWorker:
    """
    Адаптированная версия Worker_dep_geo без PyQt5
    """
    
    def __init__(self, setting_dict: dict, list_task: List[str], start_date: str, 
                 finish_date: str, master_task: Optional[str] = None, 
                 type: str = 'create'):
        self.setting_dict = setting_dict
        self.list_task = list_task
        self.geo_dep_task = geo_dep_task # Нужно будет заполнить шаблонами задач
        self.start_date = start_date
        self.finish_date = finish_date
       
        self.master_task = master_task
        self.type = type
        self.id_user = None
        self.mail = None
        self.jira = None
        
        # Колбэки для отслеживания прогресса
        self.on_progress = None
        self.on_progress_bar = None
        self.on_error = None
        self.on_complete = None
    
    def set_callbacks(self, on_progress=None, on_progress_bar=None, on_error=None, on_complete=None):
        """Установка колбэков для отслеживания прогресса"""
        self.on_progress = on_progress
        self.on_progress_bar = on_progress_bar
        self.on_error = on_error
        self.on_complete = on_complete
    
    def _emit_progress(self, message: str):
        """Эмиссия прогресса"""
        if self.on_progress:
            self.on_progress(message)
        print(f"Progress: {message}")
    
    def _emit_progress_bar(self, value: int):
        """Эмиссия прогресса бара"""
        if self.on_progress_bar:
            self.on_progress_bar(value)
    
    def _emit_error(self, error: str):
        """Эмиссия ошибки"""
        if self.on_error:
            self.on_error(error)
        print(f"Error: {error}")
    
    def _emit_complete(self, result: Any):
        """Эмиссия завершения"""
        if self.on_complete:
            self.on_complete(result)
    
    def run(self):
        """Основной метод выполнения"""
        try:
            # Расчет дедлайнов
            
            res_dict = self.setting_dict 
            
            # Загрузка данных пользователя
            with open('data.json', encoding='utf-8') as file:
                data = json.load(file)
                self.id_user = data['accountId']
                self.mail = data['mail']
            
            # Подключение к Jira
            self.jira = JIRA(server=data['server'], basic_auth=(data['mail'], data['token']))
            
            count = 1
            self._emit_progress_bar(count)
            
            # Подготовка плейсхолдеров для ссылок
            res_dict['email_task_link'] = '{{ email_task_link }}'
            res_dict['resize_task_link'] = '{{ resize_task_link }}'
            res_dict['main_task'] = '{{ main_task }}'
            res_dict['replacment_task_link'] = '{{ replacment_task_link }}'
            res_dict['task_translate_link'] = '{{ task_translate_link }}'
            
            main_list = []
            for_link_data = {}
            
            print(res_dict)
            
            # Обработка задач
            for task in self.geo_dep_task:
                count += 1
                self._emit_progress_bar(count)
                
                if task in self.list_task:
                    if task == 'main_task':
                        self._process_main_task(task, res_dict, main_list, for_link_data)
                        print("Данные собраны по мейн таске")
                    elif task == 'resize_task_link':
                        self._process_resize_task(task, res_dict, main_list, for_link_data)
                        print("Данные собраны по resize таске")
                    elif task == 'email_task_link':
                        self._process_email_task(task, res_dict, main_list, for_link_data)
                        print("Данные собраны по email таске")
                    elif task == 'setting_task_link':
                        self._process_setting_task(task, res_dict, main_list, for_link_data)
                        print("Данные собраны по setting таске")
                    elif task == 'task_translate_link':
                        self._process_translate_task(task, res_dict, main_list, for_link_data)
                        print("Данные собраны по translate таске")
            
            # Создание задач и получение ссылок
            link_dict = self._create_tasks_and_links(for_link_data)
            
            # Создание связей между задачами
            links_task = self._create_task_links(link_dict, count)
            
            res_dict = res_dict | links_task
            
            # Обновление описаний задач с актуальными ссылками
            self._update_task_descriptions(link_dict, res_dict, for_link_data, count)
            
            # Определение основной ссылки для возврата
            if 'main_task' in link_dict:
                main_link = link_dict['main_task']['link'].split('|')[1]
            else:
                first_key, first_value = next(iter(link_dict.items()))
                main_link = first_value['link'].split('|')[1]
            
            self._emit_progress(main_link)
            self._emit_complete({
                'success': True,
                'main_link': main_link,
                'all_links': link_dict,
                'message': 'Задачи успешно созданы'
            })
            
            print('End thread')
            
        except Exception as ex:
            self._emit_error(str(ex))
            print(ex)
    
    def _process_main_task(self, task: str, res_dict: dict, main_list: list, for_link_data: dict):
        """Обработка основной задачи"""
        data = self.jira.issue(self.geo_dep_task[task]['pattern'], fields='summary,description')
        disc = self.get_template(data=data.fields.description, keys=res_dict)
        summ = self.get_template(data=data.fields.summary, keys=res_dict)
        
        self.geo_dep_task[task]['fields']['description'] = disc
        self.geo_dep_task[task]['fields']['assignee']['accountId'] = self.id_user
        self.geo_dep_task[task]['fields']['summary'] = summ
        self.geo_dep_task[task]['fields']['duedate'] = res_dict['msngr_placement_deadline']
        self.geo_dep_task[task]['fields']['labels'] = ['deposit_geo', res_dict['project'], 'Мессенджер/Пуш']
        self.geo_dep_task[task]['fields']['customfield_10617'][0]['value'] = res_dict['project']
        self.geo_dep_task[task]['fields']['parent']['key'] = res_dict['parent']
        
        main_list.append(self.geo_dep_task[task]['fields'])
        for_link_data[task] = self.geo_dep_task[task]['fields']
    
    def _process_resize_task(self, task: str, res_dict: dict, main_list: list, for_link_data: dict):
        """Обработка задачи изменения размера"""
        data = self.jira.issue(self.geo_dep_task[task]['pattern'], fields='summary,description')
        disc = self.get_template(data=data.fields.description, keys=res_dict)
        summ = self.get_template(data=data.fields.summary, keys=res_dict)
        
        self.geo_dep_task[task]['fields']['description'] = disc
        self.geo_dep_task[task]['fields']['assignee']['accountId'] = self.id_user
        self.geo_dep_task[task]['fields']['summary'] = summ
        self.geo_dep_task[task]['fields']['duedate'] = res_dict['design_task']
        self.geo_dep_task[task]['fields']['customfield_10614']['value'] = res_dict['project']
        self.geo_dep_task[task]['fields']['labels'] = [res_dict['project']]
        
        main_list.append(self.geo_dep_task[task]['fields'])
        for_link_data[task] = self.geo_dep_task[task]['fields']
    
    def _process_email_task(self, task: str, res_dict: dict, main_list: list, for_link_data: dict):
        """Обработка email задачи"""
        print("Обрабатываем email")
        data = self.jira.issue(self.geo_dep_task[task]['pattern'], fields='summary,description')
        disc = self.get_template(data=data.fields.description, keys=res_dict)
        summ = self.get_template(data=data.fields.summary, keys=res_dict)
        
        self.geo_dep_task[task]['fields']['description'] = disc
        self.geo_dep_task[task]['fields']['assignee']['accountId'] = self.id_user
        self.geo_dep_task[task]['fields']['customfield_10610']['accountId'] = manager_pr[res_dict['project']]
        print("Обработан первая потенциальная ошибка")
        self.geo_dep_task[task]['fields']['summary'] = summ
        self.geo_dep_task[task]['fields']['duedate'] = res_dict['email_task']
        self.geo_dep_task[task]['fields']['customfield_10603'] = res_dict['email_task']
        self.geo_dep_task[task]['fields']['labels'] = [res_dict['project']]
        print("Обработан вторая потенциальная ошибка")
        self.geo_dep_task[task]['fields']['customfield_10617'][0]['value'] = res_dict['project']
        print("Обработан третья потенциальная ошибка")
        main_list.append(self.geo_dep_task[task]['fields'])
        for_link_data[task] = self.geo_dep_task[task]['fields']
    
    def _process_setting_task(self, task: str, res_dict: dict, main_list: list, for_link_data: dict):
        """Обработка задачи настройки"""
        data = self.jira.issue(self.geo_dep_task[task]['pattern'], fields='summary,description')
        disc = self.get_template(data=data.fields.description, keys=res_dict)
        summ = self.get_template(data=data.fields.summary, keys=res_dict)
        
        self.geo_dep_task[task]['fields']['description'] = disc
        self.geo_dep_task[task]['fields']['assignee']['accountId'] = self.id_user
        self.geo_dep_task[task]['fields']['summary'] = summ
        self.geo_dep_task[task]['fields']['duedate'] = res_dict['setting_task']
        self.geo_dep_task[task]['fields']['labels'] = [res_dict['project']]
        self.geo_dep_task[task]['fields']['customfield_10617'][0]['value'] = res_dict['project']
        
        main_list.append(self.geo_dep_task[task]['fields'])
        for_link_data[task] = self.geo_dep_task[task]['fields']
    
    def _process_translate_task(self, task: str, res_dict: dict, main_list: list, for_link_data: dict):
        """Обработка задачи перевода"""
        data = self.jira.issue(self.geo_dep_task[task]['pattern'], fields='summary,description')
        disc = self.get_template(data=data.fields.description, keys=res_dict)
        summ = self.get_template(data=data.fields.summary, keys=res_dict)
        
        self.geo_dep_task[task]['fields']['description'] = disc
        self.geo_dep_task[task]['fields']['assignee']['accountId'] = self.id_user
        self.geo_dep_task[task]['fields']['summary'] = summ
        self.geo_dep_task[task]['fields']['duedate'] = res_dict['local_task']
        self.geo_dep_task[task]['fields']['labels'] = [res_dict['project']]
        self.geo_dep_task[task]['fields']['customfield_11400'][0]['value'] = res_dict['project']
        self.geo_dep_task[task]['fields']['customfield_10633'] = [{'value': 'Английский'}]
        
        main_list.append(self.geo_dep_task[task]['fields'])
        for_link_data[task] = self.geo_dep_task[task]['fields']
    
    def _create_tasks_and_links(self, for_link_data: dict) -> dict:
        """Создание задач и получение ссылок"""
        link_dict = {}
        
        if 'main_task' in self.list_task:
            main_task_issue = self.jira.create_issue(fields=for_link_data['main_task'])
            link_dict['main_task'] = {
                'link': f'[https://jetmail.atlassian.net/browse/{main_task_issue.key}|https://jetmail.atlassian.net/browse/{main_task_issue.key}|smart-link]',
                'key': main_task_issue.key
            }
        
        if 'resize_task_link' in self.list_task:
            text_task_issue = self.jira.create_issue(fields=for_link_data['resize_task_link'])
            link_dict['resize_task_link'] = {
                'link': f'[https://jetmail.atlassian.net/browse/{text_task_issue.key}|https://jetmail.atlassian.net/browse/{text_task_issue.key}|smart-link]',
                'key': text_task_issue.key
            }
        
        if 'email_task_link' in self.list_task:
            email_task_issue = self.jira.create_issue(fields=for_link_data['email_task_link'])
            link_dict['email_task_link'] = {
                'link': f'[https://jetmail.atlassian.net/browse/{email_task_issue.key}|https://jetmail.atlassian.net/browse/{email_task_issue.key}|smart-link]',
                'key': email_task_issue.key
            }
        
        if 'setting_task_link' in self.list_task:
            setting_task_issue = self.jira.create_issue(fields=for_link_data['setting_task_link'])
            link_dict['setting_task_link'] = {
                'link': f'[https://jetmail.atlassian.net/browse/{setting_task_issue.key}|https://jetmail.atlassian.net/browse/{setting_task_issue.key}|smart-link]',
                'key': setting_task_issue.key
            }
        
        if 'task_translate_link' in self.list_task:
            task_translate_issue = self.jira.create_issue(fields=for_link_data['task_translate_link'])
            link_dict['task_translate_link'] = {
                'link': f'[https://jetmail.atlassian.net/browse/{task_translate_issue.key}|https://jetmail.atlassian.net/browse/{task_translate_issue.key}|smart-link]',
                'key': task_translate_issue.key
            }
        
        return link_dict
    
    def _create_task_links(self, link_dict: dict, count: int) -> dict:
        """Создание связей между задачами"""
        links_task = {}
        
        for item in link_dict:
            count += 1
            self._emit_progress_bar(count)
            print(item)
            
            links_task[item] = link_dict[item]['link']
            
            if item != 'main_task' and 'main_task' in link_dict:
                self.jira.create_issue_link(
                    type='causes', 
                    inwardIssue=link_dict['main_task']['key'], 
                    outwardIssue=link_dict[item]['key']
                )
            
            if item == 'task_translate_link' and 'task_translate_link' in link_dict and 'design_task_link' in link_dict:
                self.jira.create_issue_link(
                    type='relates to', 
                    inwardIssue=link_dict['task_translate_link']['key'], 
                    outwardIssue=link_dict['design_task_link']['key']
                )
            
            if item != 'email_task_link' and item != 'main_task' and 'email_task_link' in link_dict:
                self.jira.create_issue_link(
                    type='is blocked by', 
                    inwardIssue=link_dict['email_task_link']['key'], 
                    outwardIssue=link_dict[item]['key']
                )
        
        print(links_task)
        return links_task
    
    def _update_task_descriptions(self, link_dict: dict, res_dict: dict, for_link_data: dict, count: int):
        """Обновление описаний задач с актуальными ссылками"""
        for item in link_dict:
            count += 1
            self._emit_progress_bar(count)
            
            data = self.jira.issue(link_dict[item]['key'], fields='summary,description')
            disc = self.get_template(data=data.fields.description, keys=res_dict)
            issue = self.jira.issue(link_dict[item]['key'])
            for_link_data[item]['description'] = disc
            issue.update(fields=for_link_data[item])
    
    def get_meta_data(self, key: str) -> List[List[str]]:
        """Получение метаданных для создания задач"""
        with open('data.json', encoding='utf-8') as file:
            data = json.load(file)
        
        jira = JIRA(server=data['server'], basic_auth=(data['mail'], data['token']))
        createmeta = jira.createmeta(
            projectKeys=key, 
            issuetypeNames='Task', 
            expand='projects.issuetypes.fields'
        )
        
        required_fields = []
        for project in createmeta['projects']:
            for issuetype in project['issuetypes']:
                for field_id, field_info in issuetype['fields'].items():
                    required_fields.append([field_info['name'], field_id])
        
        return required_fields
    
    def get_template(self, data: str, keys: dict) -> str:
        """Рендеринг шаблона с подстановкой значений"""
        template_disc = Template(data)
        rendered_disc = template_disc.render(keys)
        return rendered_disc
    
    def get_locate(self, locals_list: List[str]) -> List[Dict[str, str]]:
        """Получение списка локализаций"""
        res_list = []
        for local in locals_list:
            if local in lang_dict:
                res_list.append({'value': lang_dict[local]})
        return res_list


# Функция для удобного использования
def create_geo_dep_tasks(setting_dict: dict, list_task: List[str], start_date: str, 
                        finish_date: str, master_task: Optional[str] = None, 
                        type: str = 'create', callbacks: Optional[dict] = None) -> dict:
    """
    Удобная функция для создания задач ГЕО-депозитки
    
    Args:
        setting_dict: Словарь настроек
        list_task: Список задач для создания
        start_date: Дата начала
        finish_date: Дата окончания
        app_version: Версия приложения
        master_task: Основная задача (опционально)
        type: Тип операции
        callbacks: Словарь с колбэками (on_progress, on_progress_bar, on_error, on_complete)
    
    Returns:
        Словарь с результатом выполнения
    """
    worker = GeoDepWorker(
        setting_dict=setting_dict,
        list_task=list_task,
        start_date=start_date,
        finish_date=finish_date,
        master_task=master_task,
        type=type
    )
    
    if callbacks:
        worker.set_callbacks(**callbacks)
    
    result = {'success': False, 'error': None}
    
    def on_complete(data):
        result.update(data)
    
    def on_error(error):
        result['error'] = error
    
    worker.set_callbacks(on_complete=on_complete, on_error=on_error)
    worker.run()
    
    return result
