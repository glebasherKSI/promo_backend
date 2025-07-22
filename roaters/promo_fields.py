from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from utils.deadline_calc import deadline_calc_dict
from Task_creator.geo_dep import create_geo_dep_tasks

router = APIRouter(prefix="/api/promo-fields", tags=["promo-fields"])

class PromoFieldsGeoDep(BaseModel):
    startDate: str
    endDate: str
    promoType: str
    project: str
    checkedTasks: List[str]
    promoFields: Dict[str, str]
    depositType: str
 
    
    @validator('startDate', 'endDate')
    def validate_dates(cls, v):
        if not v:
            return v
        try:
            # Поддержка разных форматов дат
            if 'T' in v:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            elif ' ' in v:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            else:
                datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Дата должна быть в формате ISO datetime, YYYY-MM-DD HH:MM:SS или YYYY-MM-DD')
    
    @validator('promoType', 'project')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('Поле не может быть пустым')
        return v.strip()
    
    @validator('checkedTasks')
    def validate_checked_tasks(cls, v):
        if not v:
            raise ValueError('Список задач не может быть пустым')
        return v
    
    @validator('promoFields')
    def validate_promo_fields(cls, v):
        if not v:
            raise ValueError('Поля промо не могут быть пустыми')
        return v

@router.post("/geodep")
async def create_geo_dep_promo(promo_data: PromoFieldsGeoDep):
    """
    Создать промо-акцию типа ГЕО-депозитка
    """
    try:
        if promo_data.depositType == 'common':
            dict_param ={}
            # Преобразуем дату из формата "2025-07-28 00:00:00" в "28-07-2025"
            dict_param['project'] = promo_data.project
            dict_param['geo'] = promo_data.promoFields.get('Введите гео')
            dict_param['month'] = promo_data.promoFields.get('Введите месяц')
            dict_param['number_queue'] = promo_data.promoFields.get('Введите номер очереди')
            dict_param['geo_name'] = promo_data.promoFields.get('Введите имя локали')
            dict_param['geo_users'] = promo_data.promoFields.get('Введите группу пользователей')
            dict_param['bonus_codes'] = promo_data.promoFields.get('Введите бонус коды')
            dict_param['slots'] = promo_data.promoFields.get('Введите слоты')
            dict_param['utm_metka'] = promo_data.promoFields.get('UTM-метка')
            dict_param['url_news'] = promo_data.promoFields.get('URL-новости')
            dict_param['geo_local'] = promo_data.promoFields.get('Введите локальные гео')
            dict_param['locals'] = promo_data.promoFields.get('Введите гео(коды стран)').split('(')[1].replace(')','')
            dict_param['parent'] = promo_data.promoFields.get('Ссылка на задачу родителя').split('/')[-1]
            dict_param['valutnia_formula'] = f"[документ с валютной формулой|{promo_data.promoFields.get('Введите ссылку на документ с валютной формулой')}]"
            dict_param['date_start'] = datetime.strptime(promo_data.startDate, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
            dict_param ['date_finish'] = datetime.strptime(promo_data.endDate, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")
            dict_param ['date_start_utc'] = datetime.strptime(promo_data.startDate, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M")
            dict_param ['time_start_utc'] = datetime.strptime(promo_data.startDate, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
            dict_param ['time_start'] = datetime.strptime(promo_data.startDate, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
            dict_param ['date_finish_utc'] = datetime.strptime(promo_data.endDate, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M")
            dict_param['taimer_del'] = datetime.strptime(promo_data.endDate, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y %H:%M")
            dict_deadline = deadline_calc_dict(dict_param['project'],datetime.strptime(promo_data.startDate, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M"),datetime.strptime(promo_data.endDate, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M"))
            dict_param = dict_deadline | dict_param
            # Формируемсписок задач для создания из promo_data.checkedTasks
            list_task = promo_data.checkedTasks
            # Получаем даты старта и окончания
            start_date = promo_data.startDate
            finish_date = promo_data.endDate

            # Вызываем функцию создания задач
            result = create_geo_dep_tasks(
                setting_dict=dict_param,
                list_task=list_task,
                start_date=start_date,
                finish_date=finish_date,

            )

            if not result.get('success'):
                raise HTTPException(
                    status_code=500,
                    detail=f"Ошибка создания задач: {result.get('error', 'Неизвестная ошибка')}"
                )
            return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка создания промо-акции: {str(e)}"
        ) 