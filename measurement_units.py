"""UI units: kg and metres; existing database remains grams and centimetres."""
from decimal import Decimal, InvalidOperation

FACTORS={'weight_g':1000,'height_cm':100,'width_cm':100,'length_cm':100}

def display_measurement(key,value):
    if value is None:return ''
    return format(Decimal(str(value))/FACTORS[key],'f').replace('.',',')

def stored_measurement(key,text):
    text=text.strip()
    if not text:return None
    try:
        value=Decimal(text.replace(',','.'))*FACTORS[key]
        if not value.is_finite() or value<=0:raise ValueError()
        return format(value,'f')
    except (InvalidOperation,ValueError) as exc:
        raise ValueError('Peso e dimensões devem ser números maiores que zero, ou deixe em branco.') from exc
