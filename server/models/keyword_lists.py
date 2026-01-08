KEYWORDS = {
    # 1.) Рабочая активность
    'work': {
        # 1.1.) Разработка и программирование
        'development': [
            'Visual Studio Code', 'VS Code', 'PyCharm', 'IntelliJ IDEA', 
            'Eclipse', 'WebStorm', 'GitHub', 'GitLab', 'Bitbucket', 
            'commit', 'push', 'pull', 'merge', 'repository', 
            'terminal', 'cmd', 'powershell', 'bash', 'console', 
            'command line', 'debug', 'breakpoint', 'debugging', 
            'stack trace', 'python', 'javascript', 'java', 'c++', 
            'c#', 'php', 'html', 'css', 'react', 'angular', 
            'node.js', 'function', 'class', 'module', 'package', 
            'import', 'export', 'constructor', 'docker', 'kubernetes', 
            'container', 'image', 'docker-compose'
        ],
        # 1.2.) Офисные приложения и документы
        'office': [
            'Microsoft Word', 'Document', 'Docx', '.doc', 
            'Microsoft Excel', 'Spreadsheet', '.xlsx', 'formula', 
            'sheet', 'cell', 'Microsoft PowerPoint', 'Presentation', 
            '.pptx', 'slide', 'Google Docs', 'Google Sheets', 
            'Google Slides', 'Adobe Acrobat', 'PDF', '.pdf', 
            'portable document', 'Notepad++', 'Sublime Text', 'Atom'
        ],
        # 1.3.) Деловая коммуникация
        'communication': [
            'Slack', 'Microsoft Teams', 'Zoom', 'Skype for Business', 
            'Webex', 'Jira', 'Trello', 'Asana', 'Notion', 'Confluence', 
            'task', 'issue', 'project', 'Outlook', 'Thunderbird', 
            'email', 'inbox', 'message', 'reply', 'forward', 
            'calendar', 'meeting', 'appointment', 'schedule', 
            'conference call'
        ],
        # 1.4.) Браузер (рабочие сайты)
        'browser_work': [
            'company.com', 'corporate', 'intranet', 'internal', 
            'stackoverflow', 'stack exchange', 'github', 'gitlab', 
            'bitbucket', 'docs.microsoft.com', 'developer.', 
            'api documentation', 'aws console', 'azure portal', 
            'google cloud platform', 'jira.', 'confluence.', 
            'trello.', 'asana.'
        ]
    },
    
    # 2.) Нерабочая активность (отвлекающие действия)
    'non_work': {
        # 2.1.) Социальные сети и развлечения
        'social': [
            'Facebook', 'Instagram', 'Twitter', 'X', 'TikTok', 
            'VK', 'VKontakte', 'VK.com', 'VK Video', 'OK.ru', 
            'Odnoklassniki', 'Telegram', 'WhatsApp Web', 'YouTube', 
            'Rutube', 'Netflix', 'Twitch', 'Spotify', 'Apple Music', 
            'Yandex Music', 'VK Music', 'Reddit', '9gag', 'Pikabu', 
            'meme', 'memes'
        ],
        # 2.2.) Новости и СМИ
        'news': [
            'news', 'новости', 'rbc', 'ria', 'tass', 'vedomosti', 
            'Kommersant', 'cnn', 'bbc', 'fox news', 'reuters', 
            'associated press', 'sports', 'спорт', 'football', 
            'футбол', 'soccer', 'basketball', 'баскетбол', 
            'hockey', 'хоккей'
        ],
        # 2.3.) Игры и развлечения
        'games': [
            'Steam', 'Epic Games', 'Origin', 'Battle.net', 'Xbox', 
            'Counter-Strike', 'CS', 'Dota', 'League of Legends', 
            'WoW', 'Minecraft', 'game', 'игра', 'launch', 'playing', 
            'lobby', 'match', 'level'
        ],
        # 2.4.) Личные дела и покупки
        'personal': [
            'amazon', 'ebay', 'aliexpress', 'ozon', 'wildberries', 
            'магазин', 'banking', 'банк', 'сбер', 'тинькофф', 
            'альфа-банк', 'booking', 'aviasales', 'hotels', 
            'gmail', 'yahoo mail', 'personal email'
        ]
    },
    
    # 3.) Вредоносные сайты (запрещенная активность)
    'harmful': {
        # 3.1.) Торренты и пиратство
        'piracy': [
            'uTorrent', 'BitTorrent', 'qBittorrent', 'Torrent', 
            '.torrent', 'pirate', 'piracy', 'crack', 'keygen', 
            'serial', 'activation', 'rutracker', 'rutor', 
            'kickass', 'thepiratebay'
        ],
        # 3.2.) Анонимайзеры и VPN
        'anonymizers': [
            'VPN', 'proxy', 'tor browser', 'anonymous', 'hide IP', 
            'bypass', 'unblock', 'circumvent', 'restriction'
        ],
        # 3.3.) Несанкционированное ПО
        'unauthorized': [
            'cheat', 'hack', 'trainer', 'exploit', 'mod menu', 
            'remote access', 'teamviewer', 'anydesk', 'cryptocurrency', 
            'bitcoin', 'miner', 'mining'
        ]
    },
    
    # 4.) Нейтральная / Системная активность
    'neutral': {
        # 4.1.) Системные окна
        'system': [
            'File Explorer', 'Проводник', 'Finder', 'Desktop', 
            'Рабочий стол', 'Settings', 'Настройки', 'Control Panel', 
            'Панель управления', 'Task Manager', 'Диспетчер задач', 
            'System Monitor', 'Windows Update', 'Обновление Windows'
        ],
        # 4.2.) Браузер (нейтральные страницы)
        'browser_neutral': [
            'google.com', 'yandex.ru', 'mail.', 'почта.', 'search', 
            'поиск', 'browser', 'браузер', 'new tab', 'новая вкладка', 
            'download', 'загрузка', 'downloads', 'загрузки'
        ]
    }
}

CATEGORY_MAPPING = {
    'work': 'Рабочая активность',
    'non_work': 'Нерабочая активность',
    'harmful': 'Вредоносные сайты',
    'neutral': 'Нейтральная / Системная активность',
    'unknown': 'Неизвестная активность'
}

SUBCATEGORY_MAPPING = {
    'development': 'Разработка и программирование',
    'office': 'Офисные приложения и документы',
    'communication': 'Деловая коммуникация',
    'browser_work': 'Браузер (рабочие сайты)',
    'social': 'Социальные сети и развлечения',
    'news': 'Новости и СМИ',
    'games': 'Игры и развлечения',
    'personal': 'Личные дела и покупки',
    'piracy': 'Торренты и пиратство',
    'anonymizers': 'Анонимайзеры и VPN',
    'unauthorized': 'Несанкционированное ПО',
    'system': 'Системные окна',
    'browser_neutral': 'Браузер (нейтральные страницы)'
}
