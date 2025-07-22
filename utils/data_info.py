data_type_promo = ['Турнир',"Акция","Депозитка","Бездепозитка"]
api_key_trello = "9721110ac1885383c2a4a3af13fc150f"
token_trello = 'ATTA1cbca81851c0fc0c2b5faa78e73132f34491cedc9f293dea06a1a282c8070fb309E1268C'
secret_trello = '9eca68cc10f991f6fa58215f79859dd3ae43f727b671c33177cb487134b29c84'
link_project = {
    # 'ROX':'roxcasino',
    'SOL':'solcasino',
    'JET':'jetcasino',
    'FRESH':'freshcasino',
    'IZZI':'izzicasino',
    'Legzo':'legzocasino',
    'STARDA':'stardacasino',
    'DRIP':'dripcasino',
    'Monro':'monrocasino',
    '1GO':'1gocasino',
    'LEX':'lex-casino',
    'Gizbo':'gizbocasino',
    'Irwin':'irwincasino',
    'FLAGMAN':'flagmancasino',
    'Martin':'martin-casino'   
}

managers = {
    'Владислав Князюк':'629db28476c0360069f262e2',
    'Алеся Соколовская':'712020:afd492ed-54d6-4f0a-ad3c-09be5b25fb60',
    'Каролина Есепенок':'712020:22af11c1-617f-4dd5-aa30-f6613ca91fc9',
    'Олег Калиновский':'5e4cfad42110470c8da1f1d2',
    "Евгений Радкевич": "712020:55e980e4-078b-44b1-ae5c-25def3696681",
    "Алёна Мухатдинова": "712020:37b0ba83-dd1b-4faa-b057-86b184733962",
    "Юлия Северина": "712020:c876ec97-b4ab-4ad1-a55a-27ac48f5ae0a",
}
manager_pr = {
    'IZZI':managers['Алеся Соколовская'],
    "DRIP":managers['Алеся Соколовская'],
    "ROX":managers['Евгений Радкевич'],
    "FRESH":managers['Владислав Князюк'],
    "Legzo":managers['Каролина Есепенок'],
    "STARDA":managers['Владислав Князюк'],
    "Monro":managers['Каролина Есепенок'],
    "1GO":managers['Алёна Мухатдинова'],
    "LEX":managers['Юлия Северина'],
    "VOLNA":managers['Евгений Радкевич'],
    "SOL":managers['Владислав Князюк'],
    "JET":managers['Владислав Князюк'],
    "Gizbo":managers['Владислав Князюк'],
    "Irwin":managers['Владислав Князюк'],
    "FLAGMAN":managers['Владислав Князюк'],
    "Martin":managers['Олег Калиновский']
}
lang_dict = {
    'EN':'Английский',
    'UA':'Украинский',
    'KZ':'Казахский',
    'FR':'Французский',
    'DE':'Немецкий',
    'FI':'Финский',
    'ES':'Испанский',
    'PT':'Португальский',
    'TR':'Турецкий',
    'JA':'Японский',
    'DA':'Датский',
    'NO':'Норвежский',
    'PL':'Польский'
}
geo_dep_task = {
    'main_task':{
    'pattern':'PRMR-11901',
    "fields":{
        'project': {'key': 'PRMR'},
        'parent':{'key': 'PARENT-123'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
    'setting_task_link':{
    'pattern':'PRMR-11905',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
    'resize_task_link':{
    'pattern':'DSGN-16781',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId': None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }},
    
    'email_task_link':{
    'pattern':'PRMR-11903',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
    'task_translate_link':{
    'pattern':'CONT-28825',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }}
    
    
}
geo_segment_dep_task = {
    'main_task':{
    'pattern':'PRMR-37945',
    "fields":{
        'project': {'key': 'PRMR'},
        'parent':{'key': 'PARENT-123'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
    'setting_task_link':{
    'pattern':'PRMR-37960',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
    'resize_task_link':{
    'pattern':'DSGN-16781',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId': None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }},
    
    'email_task_link':{
    'pattern':'PRMR-37956',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
    'task_translate_link':{
    'pattern':'CONT-28825',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }}
    
    
}

cis_dep_task = {
    'main_task':{
    'pattern':'PRMR-11990',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
    'mess_push_task':{
    'pattern':'PRMR-33948',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
    'setting_task_link':{
    'pattern':'PRMR-1051',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
    'design_task_link':{
    'pattern':'DSGN-15796',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId': None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }},
    
    'email_task_link':{
    'pattern':'PRMR-11992',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
    'task_translate_link':{
    'pattern':'CONT-29062',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }},
    'text_task_link':{
    'pattern':'CONT-29060',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'RuCopy'},
        'duedate': None,
        'labels' : None
    }
}, 'resize_task_link':{
    'pattern':'DSGN-17816',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId': None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }}
    
    
}
tournament_task = {
'main_task':{
    'pattern':{
        'local':'PRMR-11792',
        'network':'PRMR-20824'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'mess_push_task':{
    'pattern':{
        'local':'PRMR-33935',
        'network':'PRMR-33940'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'text_task_link':{
    'pattern':{
        'local':'CONT-28616',
        'network':'CONT-39457'
        },
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'RuCopy'},
        'duedate': None,
        'labels' : None
    }
},
'email_task_link':{
    'pattern':{
        'local':'PRMR-11815',
        'network':'PRMR-20827'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
'setting_task_link':{
    'pattern':{
        'local':'PRMR-1050',
        'network':'PRMR-20826'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
'design_task_link':{
    'pattern':{
        'local':'DSGN-15658',
        'network':'DSGN-20399'
        },
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId':None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
'replacment_task_link':{
    'pattern':{
        'local':'IT-79922',
        'network':'IT-92666'
        },
    "fields":{
        'project': {'key': 'IT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'customfield_11499':{'value':'Other'},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Content'},
        'duedate': None,
        'labels' : None
    }
},
'task_translate_link':{
    'pattern':{
        'local':'CONT-28629',
        'network':'CONT-39459'
        },
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }
}

}
info_tasks_provaider = {
   'main_task':{
    'pattern':'PRMR-12055',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'mess_push_task':{
    'pattern':'PRMR-33950',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'text_task_link':{
    'pattern':'CONT-29150',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'RuCopy'},
        'duedate': None,
        'labels' : None
    }
},
'email_task_link':{
    'pattern':'PRMR-12056',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
'design_task_link':{
    'pattern':'DSGN-15833',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId':None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
'task_translate_link':{
    'pattern':'CONT-29153',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }
}
}
info_tasks_prereliz = {
   'main_task':{
    'pattern':'PRMR-12071',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'mess_push_task':{
    'pattern':'PRMR-33949',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Retention'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'text_task_link':{
    'pattern':'CONT-29200',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'RuCopy'},
        'duedate': None,
        'labels' : None
    }
},
'email_task_link':{
    'pattern':'PRMR-12072',
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
'design_task_link':{
    'pattern':'DSGN-15836',
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId':None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
'task_translate_link':{
    'pattern':'CONT-29203',
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }
}
}
action_tasks = {
'main_task':{
    'pattern':{
        'network':'PRMR-11874',
        'global':'PRMR-20876'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},
'mess_push_task':{
    'pattern':{
        'network':'PRMR-33943',
        'global':'PRMR-33944'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }},         
'text_task_link':{
    'pattern':{
        'network':'CONT-28744',
        'global':'CONT-39484'
        },
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'RuCopy'},
        'duedate': None,
        'labels' : None
    }
},
'email_task_link':{
    'pattern':{
        'network':'PRMR-11878',
        'global':'PRMR-20877'
        },
    "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'customfield_10603':None,
        'duedate': None,
        'labels' : None
    }
},
'design_task_link':{
    'pattern':{
        'network':'DSGN-15735',
        'global':'DSGN-20446'
        },
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId':None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
},
'replacment_task_link':{
    'pattern':{
        'network':'IT-80011',
        'global':'IT-92719'
        },
    "fields":{
        'project': {'key': 'IT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'customfield_11499':{'value':'Other'},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Content'},
        'duedate': None,
        'labels' : None
    }
},
'task_translate_link':{
    'pattern':{
        'network':'CONT-28750',
        'global':'CONT-39517'
        },
    "fields":{
        'project': {'key': 'CONT'},
        'assignee': {'accountId':None},
        'customfield_11400':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Promotion'},
        'duedate': None,
        'customfield_10633':None,
        'labels' : None
    }
},
'task_ss_design':{
    'pattern':{
        'network':'DSGN-16732',
        'global':'DSGN-16732'
        },
    "fields":{
        'project': {'key': 'DSGN'},
        'assignee': {'accountId':None},
        'components': [{'name': 'Графика (промо, афилка, проекты и тд)'}],
        'customfield_10614':{"value":None},
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
}
}
bezdep_tasks = {
    'bezdep':{
        'main_task':{
        'pattern':'PRMR-12047',
        "fields":{
            'project': {'key': 'PRMR'},
            'assignee': {'accountId':None},
            'customfield_10691': {"id":'10392'},# Категория задач PRMR*
            'components': [{'name': 'Promo'}],
            'customfield_10617':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'Task'},
            'duedate': None,
            'labels' : None
         }
        },
        'email_task_link':{
        'pattern':'PRMR-12052',
        "fields":{
            'project': {'key': 'PRMR'},
            'assignee': {'accountId':None},
            'customfield_10610':{'accountId':None},
            'customfield_10691': {"id":'10392'},# Категория задач PRMR*
            'components': [{'name': 'Delivery'}],
            'customfield_10617':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'Task'},
            'duedate': None,
            'labels' : None
    }
        },
        'setting_task_link':{
            'pattern':'PRMR-1180',
            "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
        },
        'task_translate_link':{
        'pattern':'CONT-29145',
        "fields":{
            'project': {'key': 'CONT'},
            'assignee': {'accountId':None},
            'customfield_11400':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'Promotion'},
            'duedate': None,
            'customfield_10633':None,
            'labels' : None
    }

    },
    'text_task_link':{
        'pattern':'CONT-29143',
        "fields":{
            'project': {'key': 'CONT'},
            'assignee': {'accountId':None},
            'customfield_11400':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'RuCopy'},
            'duedate': None,
            'labels' : None
        }
    }
    },
    'bezdep_segment':{
        'main_task':{
            'pattern':'PRMR-12009',
             "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }
        },
        'email_task_link':{
            'pattern':'PRMR-12010',
            "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
        },
        'setting_task_link':{
            'pattern':'PRMR-1184',
            "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
        },
        'task_translate_link':{
        'pattern':'CONT-29089',
        "fields":{
            'project': {'key': 'CONT'},
            'assignee': {'accountId':None},
            'customfield_11400':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'Promotion'},
            'duedate': None,
            'customfield_10633':None,
            'labels' : None
    }

    }
    },
    'bezdep_geo':{
        'main_task':{
            'pattern':'PRMR-11981',
             "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Promo'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
         }
        },
        'email_task_link':{
            'pattern':'PRMR-11982',
            "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10610':{'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Delivery'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
        },
        'setting_task_link':{
            'pattern':'PRMR-11983',
            "fields":{
        'project': {'key': 'PRMR'},
        'assignee': {'accountId':None},
        'customfield_10691': {"id":'10392'},# Категория задач PRMR*
        'components': [{'name': 'Bonus operation'}],
        'customfield_10617':[{"value":None}],
        'summary': None,
        'description':None,
        'issuetype': {'name': 'Task'},
        'duedate': None,
        'labels' : None
    }
        },
        'task_translate_link':{
        'pattern':'CONT-29041',
        "fields":{
            'project': {'key': 'CONT'},
            'assignee': {'accountId':None},
            'customfield_11400':[{"value":None}],
            'summary': None,
            'description':None,
            'issuetype': {'name': 'Promotion'},
            'duedate': None,
            'customfield_10633':None,
            'labels' : None
    }

    }
    }
    
}


#"ATATT3xFfGF0sEUoBe0Pk6lUEYFupDGF4SXQ2dVdT2EfzAhewpe6dg-_d83928SgN9mN12ICnTnuCKUStAI3mXRymn0ppgr2jH3yFaV9e7WD2qSdmOCrjJb1n3h6MV5EHCZ0oAX5tcoO_QQqoOB1I9hh2gPrv2rkJZh-pnr29jCUxRvA0lXVPWw=99BEEDBB"