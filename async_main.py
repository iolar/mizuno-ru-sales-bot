import json
from bs4 import BeautifulSoup
import asyncio
import aiohttp


async def get_data(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      'Chrome/122.0.0.0 Safari/537.36',
    }
    session = aiohttp.ClientSession()

    async with session.get(url, headers=headers) as response:
        soup = BeautifulSoup(await response.text(), 'lxml')

    pages_count = int(soup.find('li', class_='bx-pag-next').find_previous_sibling().find('a').text)

    data = []

    for page in range(1, pages_count + 1):
        page_url = f'{url}?PAGEN_1={page}'

        async with session.get(page_url, headers=headers) as response:
            soup = BeautifulSoup(await response.text(), 'lxml')

        items = soup.find_all('div', class_='unproduct-container')

        for item in items:
            item_title = item.find('div', class_="name_unproduct").find('a').text.strip()
            item_url = 'https://mizuno.com.ru' + \
                       item.find('div', class_="name_unproduct").find('a').get('href')
            item_price = int(item.find('span', class_="price").text.replace(' ', '').replace('руб.', ''))
            if item.find('span', class_="old-price").get('style') == 'display: none;':
                item_old_price = ''
                item_discount = 'Нет скидки'
            else:
                item_old_price = int(item.find('span', class_="old-price").text.replace(' ', '').replace('руб.', ''))
                item_discount = round(((item_old_price - item_price) / item_old_price) * 100)

            # print(f'\n{category}')
            # print(f'{title}')
            # print(url)
            # print(f'{price}  {old_price}  {discount}\n{"-" * 30}')

            data.append(
                {
                    "Название": item_title,
                    "Ссылка": item_url,
                    "Цена": item_price,
                    "Старая цена": item_old_price,
                    "Скидка": item_discount,
                }
            )

        print(f"Обработана страница {page_url}")

    if 'muzhskaya_obuv' in url:
        category = 'Мужские кроссовки'
    elif 'zhenskaya_obuv' in url:
        category = 'Женские кроссовки'
    elif 'muzhskaya_odezhda' in url:
        category = 'Мужская одежда'
    elif 'zhenskaya_odezhda' in url:
        category = 'Женская одежда'
    else:
        category = 'Другое'

    with open(f'data/{category}.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    await session.close()


async def main():
    with open('static/mizuno.com.ru.txt') as file:
        items_urls = file.read().splitlines()

    for item_url in items_urls:

        try:
            await get_data(url=item_url)
        except Exception:
            print(f"[!] URL {item_url} unavailable!\n{'-' * 30} ")
            continue


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
