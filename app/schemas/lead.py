from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, model_validator

from app.repository.tgbot import Alert


class NotionLead(BaseModel):
    id: str
    notion_lead_id: str

    @model_validator(mode='before')
    def extract_fields(self: dict, *args, **kwargs) -> dict:
        self['id'] = str(self.get('id', ''))
        self['notion_lead_id'] = str(self.get('properties', {})
                                     .get('ID заказа в Notion', {})
                                     .get('unique_id', {})
                                     .get('number', 0))
        return self

    def to_amo_update(self, lead_id: int) -> dict:
        return {
            'id': lead_id,
            'custom_fields_values': [
                {
                    'field_id': 1450043,
                    'values': [
                        {
                            'value': self.id,
                        },
                    ],
                },
                {
                    'field_id': 1449773,
                    'values': [
                        {
                            'value': f'https://www.notion.so/cehcom/{self.id.replace('-', '')}',
                        },
                    ],
                },
                {
                    'field_id': 1450275,
                    'values': [
                        {
                            'value': f"LP-{self.notion_lead_id}",
                        },
                    ],
                },
            ],
        }


class Lead(BaseModel):
    id: int
    name: str = ''
    price: int = 0
    custom_fields: dict

    def hash(self) -> str:
        return str(hash(str(self.dict())))

    def p_status(self) -> str | None:
        return self.custom_fields.get('1450271', {}).get('values', [{}])[0].get('value', None)

    def description(self) -> str:
        return self.custom_fields.get('1407255', {}).get('values', [{}])[0].get('value', '')

    def deadline(self) -> (str, str):
        date_start = self.custom_fields.get('1421827', {}).get('values', [''])[0]
        date_end = self.custom_fields.get('1421829', {}).get('values', [''])[0]
        if date_start != '':
            date_start = (datetime.fromtimestamp(int(date_start), timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
        if date_end != '':
            date_end = (datetime.fromtimestamp(int(date_end), timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
        return date_start, date_end

    def contract_number(self) -> str:
        return self.custom_fields.get('1448499', {}).get('values', [{}])[0].get('value', '')

    def contract_link(self) -> str:
        return self.custom_fields.get('1421523', {}).get('values', [{}])[0].get('value', '')

    def bill_no(self) -> str:
        return self.custom_fields.get('1448515', {}).get('values', [{}])[0].get('value', '')

    def bill_link(self) -> str:
        return self.custom_fields.get('1448511', {}).get('values', [{}])[0].get('value', '')

    def payment_type(self) -> str:
        return self.custom_fields.get('1448521', {}).get('values', [{}])[0].get('value', '')

    def taxes(self) -> str:
        return self.custom_fields.get('1448523', {}).get('values', [{}])[0].get('value', '')

    def pay_slip(self) -> str:
        return self.custom_fields.get('1448525', {}).get('values', [{}])[0].get('value', '')

    def income(self) -> int:
        return int(self.custom_fields.get('1448935', {}).get('values', [{}])[0].get('value', 0))

    def agent_payment(self) -> int:
        return int(self.custom_fields.get('1449791', {}).get('values', [{}])[0].get('value', 0))

    def p_list(self) -> str:
        return self.custom_fields.get('1449781', {}).get('values', [{}])[0].get('value', '')

    def contact_id(self) -> str:
        id = self.custom_fields.get('1432035', {}).get('values', [{}])[0].get('value', '')
        if id:
            id = f'https://ceh.amocrm.ru/contacts/detail/{id}'
        return id

    def company_id(self) -> str:
        id = self.custom_fields.get('1450437', {}).get('values', [{}])[0].get('value', '')
        if id:
            id = f'https://ceh.amocrm.ru/companies/detail/{id}'
        return id

    def contact_uids(self) -> list[str]:
        res = self.custom_fields.get('1450459', {}).get('values', [{}])[0].get('value', '').split(',')
        if res[0] == '':
            res = []
        return res

    def company_uid(self) -> str:
        return self.custom_fields.get('1450457', {}).get('values', [{}])[0].get('value', '')

    def nid(self) -> str:
        result = self.custom_fields.get('1450275', {}).get('values', [{}])[0].get('value', '')
        return result.replace('LP-', 'C-')

    def to_notion(self) -> dict:
        description = self.description()
        date_start, date_end = self.deadline()
        contract_link = self.contract_link()
        bill_link = self.bill_link()
        taxes = self.taxes()
        pay_slip = self.pay_slip()
        income = self.income()
        p_list = self.p_list()
        payment_type = self.payment_type()
        agent_payment = self.agent_payment()
        bill_no = self.bill_no()
        contract_number = self.contract_number()
        contact_id = self.contact_id()
        company_id = self.company_id()
        contact_uids = self.contact_uids()
        company_uid = self.company_uid()
        result = {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': f'{self.nid()} / {self.name}',
                        }
                    },
                ],
            },
            'Статус сделки': {
                'status': {
                    'name': self.p_status(),
                },
            },
            'ID сделки amoCRM': {
                'number': self.id,
            },
        }
        if self.price != 0:
            result['Бюджет общий'] = {
                'number': self.price,
            }
        if date_start != '' or date_end != '':
            date = {}
            if date_start != '':
                date['start'] = date_start
            if date_end != '':
                date['end'] = date_end
            result['Дедлайн'] = {
                'date': {**date},
            }
        if contract_link != '':
            result['Договор'] = {
                'url': contract_link,
            }
        if bill_link != '':
            result['Счет на оплату'] = {
                'url': bill_link,
            }
        if taxes != '':
            result['Налоги'] = {
                'select': {
                    'name': taxes,
                },
            }
        if pay_slip != '':
            result['Расчетный счет'] = {
                'select': {
                    'name': pay_slip,
                },
            }
        if income != 0:
            result['Поступления'] = {
                'number': income,
            }
        if p_list != '':
            result['П-лист'] = {
                'url': p_list,
            }
        if payment_type != '':
            result['Вид оплаты'] = {
                'select': {
                    'name': payment_type,
                },
            }
        if description != '':
            result['Описание заказа'] = {
                'rich_text': [
                    {
                        'text': {
                            'content': description,
                        },
                    },
                ],
            }
        if agent_payment != 0:
            result['Выплатили агенту'] = {
                'number': agent_payment,
            }
        if bill_no != '':
            result['Счет №'] = {
                'rich_text': [
                    {
                        'text': {
                            'content': bill_no,
                        },
                    },
                ],
            }
        if contract_number != '':
            result['Договор №'] = {
                'rich_text': [
                    {
                        'text': {
                            'content': contract_number,
                        },
                    },
                ],
            }
        if contact_id != '':
            result['Контакт amoCRM'] = {
                'url': contact_id,
            }
        if company_id != '':
            result['Компания amoCRM'] = {
                'url': company_id,
            }
        if contact_uids:
            result['Контакты'] = {
                'relation': [
                    {
                        'id': uid,
                    } for uid in contact_uids
                ],
            }
        if company_uid != '':
            result['Компания'] = {
                'relation': [
                    {
                        'id': company_uid,
                    },
                ],
            }
        return result

    def to_notion_update(self) -> dict:
        date_start, date_end = self.deadline()
        result = {
            'Name': {
                'title': [
                    {
                        'text': {
                            'content': f'{self.nid()} / {self.name}',
                        }
                    },
                ],
            },
            'Описание заказа': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.description(),
                        },
                    },
                ],
            },
            'Дедлайн': {
                'date': {
                    'start': date_start,
                    'end': date_end if date_end else None,
                },
            },
            'Договор': {
                'url': self.contract_link() if self.contract_link() else None,
            },
            'Счет на оплату': {
                'url': self.bill_link() if self.bill_link() else None,
            },
            'Налоги': {
                'select': {'name': self.taxes()} if self.taxes() else None,
            },
            'Расчетный счет': {
                'select': {'name': self.pay_slip()} if self.pay_slip() else None,
            },
            'Поступления': {
                'number': self.income() if self.income() else None,
            },
            'П-лист': {
                'url': self.p_list() if self.p_list() else None,
            },
            'Вид оплаты': {
                'select': {'name': self.payment_type()} if self.payment_type() else None,
            },
            'Выплатили агенту': {
                'number': self.agent_payment() if self.agent_payment() else None,
            },
            'Счет №': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.bill_no(),
                        },
                    },
                ],
            },
            'Договор №': {
                'rich_text': [
                    {
                        'text': {
                            'content': self.contract_number(),
                        },
                    },
                ],
            },
            'Контакт amoCRM': {
                'url': self.contact_id() if self.contact_id() else None,
            },
            'Компания amoCRM': {
                'url': self.company_id() if self.company_id() else None,
            },
            'Контакты': {
                'relation': [
                    {
                        'id': uid,
                    } for uid in self.contact_uids()
                ],
            },
            'Компания': {
                'relation': [
                    {
                        'id': self.company_uid(),
                    },
                ] if self.company_uid() else [],
            },
            'Статус сделки': {
                'status': {
                    'name': self.p_status(),
                } if self.p_status() else None,
            },
            'Бюджет общий': {
                'number': self.price,
            },
            'ID сделки amoCRM': {
                'number': self.id,
            },
        }
        if date_start == '' and date_end != '':
            result.pop('Дедлайн')
        if date_start == '' and date_end == '':
            result['Дедлайн'] = {
                'date': None,
            }
        return result


class LeadUpdate(BaseModel):
    id: int
    custom_fields_values: list[dict]

    def hash(self) -> str:
        dict_str = json.dumps(self.dict(), sort_keys=True)
        return hashlib.md5(dict_str.encode('utf-8')).hexdigest()

    @classmethod
    def from_notion_resp(cls, data: dict) -> LeadUpdate:
        props = data['properties']
        result = dict()
        lead_id = props['ID сделки amoCRM']['number']
        if lead_id is None:
            lead_id = 0
        result['id'] = lead_id
        date_ready = props['Дата готово']['date']
        if date_ready is not None:
            date_ready = date_ready['start']
            dt = datetime.strptime(
                date_ready,
                '%Y-%m-%d'
            ).replace(
                tzinfo=timezone.utc,
            ).astimezone()
            date_ready = (dt.strftime('%Y-%m-%dT%H:%M:%S%z')[:-2] + ':'
                          + dt.strftime('%Y-%m-%dT%H:%M:%S%z')[-2:])
        result['name'] = props['Name']['title'][0]['text']['content']
        custom_fields = [
            {
                'field_id': 1450271,
                'values': [
                    {
                        'value': props['Статус сделки']['status']['name'],
                    },
                ],
            },
            {
                'field_id': 1407255,
                'values': [
                    {
                        'value': props['Описание заказа']['rich_text'][0]['text']['content']
                        if props['Описание заказа']['rich_text'] else '',
                    },
                ],
            },
            {
                'field_id': 1448935,
                'values': [
                    {
                        'value': props['Поступления']['number']
                        if props['Поступления']['number'] else 0,
                    },
                ],
            },
            {
                'field_id': 1449791,
                'values': [
                    {
                        'value': props['Выплатили агенту']['number']
                        if props['Выплатили агенту']['number'] else 0,
                    },
                ],
            },
            {
                'field_id': 1449769,
                'values': [
                    {
                        'value': date_ready,
                    },
                ] if date_ready else None,
            },
        ]
        result['custom_fields_values'] = custom_fields
        return LeadUpdate(**result)


def build_nested_dict(flat_dict):
    def set_nested_value(d, keys, value):
        for key in keys[:-1]:
            if key.isdigit():
                key = int(key)
                if isinstance(d, list):
                    if len(d) <= key:
                        d.extend([{}] * (key - len(d) + 1))
                    d = d[key]
                else:
                    d[key] = d.get(key, {})
                    d = d[key]
            else:
                if key not in d or not isinstance(d[key], dict):
                    d[key] = {}
                d = d[key]

        last_key = keys[-1]
        if last_key.isdigit():
            last_key = int(last_key)
            if isinstance(d, list):
                if len(d) <= last_key:
                    d.extend([None] * (last_key - len(d) + 1))
                d[last_key] = value
            else:
                d[last_key] = value
        else:
            d[last_key] = value

    nested_dict = {}

    for key, value in flat_dict.items():
        parts = key.replace(']', '').split('[')
        set_nested_value(nested_dict, parts, value)

    return nested_dict


def transform_custom_fields(fields: dict):
    transformed = {}
    for field_index, field_data in fields.items():
        field_id = field_data['id']
        field_data.pop('id')
        transformed[field_id] = field_data
    return transformed


def parse_lead_update(data) -> Lead | None:
    data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
    data = build_nested_dict(data)
    update = data.get('leads', {}).get('update', {})
    if not update:
        return
    if len(update) > 1:
        Alert.critical(f'`❌ Получено несколько заявок на обновление, будет обработана только первая!\n\n{update}`')
    update = update[0]
    update['custom_fields'] = transform_custom_fields(update['custom_fields'])
    return Lead(**update)
