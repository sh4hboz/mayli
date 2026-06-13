# orders/utils.py

import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

DELIVERY_ZONE_COORDS = [
    (37.238666, 67.242378),
    (37.241025, 67.251058),
    (37.2417, 67.252116),
    (37.242037, 67.253916),
    (37.242037, 67.256456),
    (37.244817, 67.261537),
    (37.24903, 67.269475),
    (37.25021, 67.272862),
    (37.25021, 67.274979),
    (37.254843, 67.273815),
    (37.25518, 67.282706),
    (37.254085, 67.285352),
    (37.253832, 67.289692),
    (37.254422, 67.295937),
    (37.254675, 67.296889),
    (37.254591, 67.297524),
    (37.254254, 67.297524),
    (37.253832, 67.297948),
    (37.253832, 67.299218),
    (37.254675, 67.300171),
    (37.256444, 67.300276),
    (37.256444, 67.302393),
    (37.256191, 67.303028),
    (37.257202, 67.305357),
    (37.256697, 67.306204),
    (37.25695, 67.308427),
    (37.258129, 67.311496),
    (37.258466, 67.315201),
    (37.258466, 67.3188),
    (37.257118, 67.335417),
    (37.253411, 67.333089),
    (37.252653, 67.334782),
    (37.251558, 67.3351),
    (37.24962, 67.333936),
    (37.248188, 67.333406),
    (37.246839, 67.332877),
    (37.244312, 67.331289),
    (37.242289, 67.328961),
    (37.239225, 67.328551),
    (37.237203, 67.328551),
    (37.235686, 67.328022),
    (37.233495, 67.325587),
    (37.232315, 67.324635),
    (37.231894, 67.323047),
    (37.231894, 67.319448),
    (37.232484, 67.31532),
    (37.231403, 67.310089),
    (37.231066, 67.30903),
    (37.229633, 67.307866),
    (37.228369, 67.307548),
    (37.227105, 67.307654),
    (37.226009, 67.307125),
    (37.224998, 67.306384),
    (37.223733, 67.305749),
    (37.222722, 67.305326),
    (37.218845, 67.304055),
    (37.217328, 67.30395),
    (37.21522, 67.304055),
    (37.214125, 67.305643),
    (37.212776, 67.307019),
    (37.21168, 67.307866),
    (37.210837, 67.307866),
    (37.20991, 67.308184),
    (37.208561, 67.309136),
    (37.205777, 67.30889),
    (37.203585, 67.308678),
    (37.202236, 67.30762),
    (37.201477, 67.306773),
    (37.199622, 67.304656),
    (37.197177, 67.301058),
    (37.195069, 67.297141),
    (37.194142, 67.294283),
    (37.195322, 67.293754),
    (37.194563, 67.292061),
    (37.195912, 67.291743),
    (37.196924, 67.291743),
    (37.197346, 67.287721),
    (37.19684, 67.284757),
    (37.196418, 67.280523),
    (37.196924, 67.276395),
    (37.198948, 67.272056),
    (37.200297, 67.268457),
    (37.201308, 67.264435),
    (37.202573, 67.262212),
    (37.205777, 67.259777),
    (37.211593, 67.255649),
    (37.214628, 67.253638),
    (37.216904, 67.254379),
    (37.220613, 67.253744),
    (37.2239, 67.253215),
    (37.227524, 67.251839),
    (37.232327, 67.248346),
    (37.235361, 67.245382),
    (37.238732, 67.242418),
    (37.238648, 67.242524),
]

def is_in_delivery_zone_raycast(lat, lng):
    """
    Pure-Python Ray-Casting algoritmi point-in-polygon tekshiruvi uchun.
    lat -> Y koordinata, lng -> X koordinata.
    """
    n = len(DELIVERY_ZONE_COORDS)
    inside = False
    p1x, p1y = DELIVERY_ZONE_COORDS[0][1], DELIVERY_ZONE_COORDS[0][0]
    for i in range(n + 1):
        p2x, p2y = DELIVERY_ZONE_COORDS[i % n][1], DELIVERY_ZONE_COORDS[i % n][0]
        if lat > min(p1y, p2y):
            if lat <= max(p1y, p2y):
                if lng <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or lng <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def assign_daily_ids(order):
    """
    daily_id va type_daily_id ni race-condition himoya bilan belgilaydi.
    Faqat yangi order (daily_id=None) uchun chaqirilsin.
    select_for_update() + transaction.atomic() orqali parallel so'rovlar
    bir xil ID olishining oldi olinadi.
    """
    today = timezone.localdate()
    with transaction.atomic():
        last = (
            order.__class__.objects
            .filter(created_at__date=today, daily_id__isnull=False)
            .select_for_update()
            .order_by('-daily_id')
            .only('daily_id')
            .first()
        )
        order.daily_id = (last.daily_id + 1) if last else 1

        if order.order_type == 'delivery':
            last_d = (
                order.__class__.objects
                .filter(
                    created_at__date=today,
                    order_type='delivery',
                    type_daily_id__isnull=False,
                )
                .select_for_update()
                .order_by('-type_daily_id')
                .only('type_daily_id')
                .first()
            )
            order.type_daily_id = (last_d.type_daily_id + 1) if last_d else 1

        order.save(update_fields=['daily_id', 'type_daily_id'])


def is_in_delivery_zone(lat, lng):
    """
    Yetkazib berish zonasi ichidami yoki yo'qligini tekshirish.
    Avval Shapely orqali harakat qiladi, muammo bo'lsa Ray-Casting algoritmiga o'tadi.
    """
    if lat is None or lng is None:
        return False
    
    try:
        from shapely.geometry import Point, Polygon
        # Shapely'da koordinatalar (longitude, latitude) / (x, y) tartibida bo'lishi tavsiya etiladi.
        # Biz (lng, lat) formatida Polygon yaratamiz.
        polygon_points = [(p[1], p[0]) for p in DELIVERY_ZONE_COORDS]
        poly = Polygon(polygon_points)
        point = Point(lng, lat)
        return poly.contains(point)
    except Exception as e:
        logger.warning(f"Shapely validatsiya xatosi: {e}. Ray-casting algoritmiga o'tilmoqda.")
        return is_in_delivery_zone_raycast(lat, lng)
