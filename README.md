# КриптоПро 5.0 в докер контейнере c расширением pycades

Содержимое контейнера:

* python 3.9.10 с установленным расширением `pycades` (`CPStore`, `CPSigner`, `CPSignedData`)
* инструменты КриптоПро: `certmgr`, `cpverify`, `cryptcp`, `csptest`, `csptestf`, `der2xer`, `inittst`, `wipefile`, `cpconfig`
* вспомогательные скрипты командой строки
* HTTP REST-сервер

Есть 3 варианта использования контейнера:

* [через интерфейс командной строки](#cli) (и ssh-клиент для удаленных машин)
* [через HTTP REST-сервер](#http)
* добавить свои обработчики внутрь контейнера

# Структура проекта

```
├── assets        - материалы для README.md
├── devel         - devel скрипты
├── certificates  - тестовые сертификаты
├── dist          - пакеты КриптоПро (необходимо скачать с официального сайта)
├── Dockerfile    - файл сборки образа
├── README.md     - этот файл
└── scripts       - вспомогательные скрипты командой строки
└── www           - HTTP REST-сервер
```

# Работа с контейнером через интерфейс командной строки

## Сборка и запуск

```sh
docker compose build
docker compose up
```

## Лицензия

Установка серийного номера:

```sh
docker compose exec -T cryptopro cpconfig -license -set <серийный_номер>
```

Просмотр:

```sh
docker compose exec -T cryptopro cpconfig -license -view
```

![license](./assets/license.gif)


## Установка корневых сертификатов

Для установки корневых сертификатов нужно на `stdin` скрипта `/scripts/root` передать файл с сертификатами. Если в файле несколько сертификатов, все они будут установлены.

### Через скачивание на диск

Скачаем сертификат на диск с помощью `curl` и передадим полученный файл на `stdin` с запуском команды его установки:

```sh
# сертификаты УЦ
curl -sS http://cpca.cryptopro.ru/cacer.p7b > certificates/cacer.p7b
cat certificates/cacer.p7b | docker compose exec -T cryptopro /scripts/root
# сертификаты тестового УЦ
curl -sS http://testca2012.cryptopro.ru/cert/rootca.cer > certificates/rootca.p7b
cat certificates/rootca.p7b | docker compose exec -T cryptopro /scripts/root
curl -sS http://testca2012.cryptopro.ru/cert/subca.cer > certificates/subca.p7b
cat certificates/subca.p7b | docker compose exec -T cryptopro /scripts/root
```

### Без скачивания на диск

```sh
# сертификаты УЦ
curl -sS http://cpca.cryptopro.ru/cacer.p7b | docker compose exec -T cryptopro /scripts/root
# сертификаты тестового УЦ
curl -sS http://testca2012.cryptopro.ru/cert/rootca.cer | docker compose exec -T cryptopro /scripts/root
curl -sS http://testca2012.cryptopro.ru/cert/subca.cer | docker compose exec -T cryptopro /scripts/root
```

![cacer](./assets/cacer.gif)

Примечание: по какой-то причине иногда "заедает", но при повторном запуске - срабатывает.

## Как создать новый тестовый сертификат для Честного Знака

- [Заходим в Тестовый Удостоверяющий Центр](http://testca2012.cryptopro.ru/ui/)
- Сертификаты - Создать
- Заполняем обязательные поля по [инструкции](https://честныйзнак.рф/business/doc/?id=Инструкция_по_созданию_тестовой_подписи.html), иначе будет ошибка при логине или регистрации
- Запросы - Изготовление - Обновить, подождать, Установить
- Установить в реестр или вставить флешку, выгрузить приватную часть
- Скачать публичный сертификат
- Скопировать папку, создать zip без корневой папки

Более подробные инструкции:
- [Инструкция по созданию тестовой подписи](./docs/Инструкция_по_созданию_тестовой_подписи.pdf)
- [Как получить рабочий сертификат КриптоПро и установить на Linux](./docs/Как%20получить%20рабочий%20сертификат%20КриптоПро%20и%20установить%20на%20Linux.pdf)

## Установка сертификатов пользователя для проверки и подписания

Необходимо специальным образом сформировать zip-архив `bundle.zip` и отправить его на `stdin` скрипта `/scripts/my`. Пример такого zip-файла:

```
├── certificate.cer - файл сертификата (не обязательно)
└── le-09650.000 - каталог с файлами закрытого ключа (не обязательно)
    ├── header.key
    ├── masks2.key
    ├── masks.key
    ├── name.key
    ├── primary2.key
    └── primary.key
```

Первый найденный файл в корне архива будет воспринят как сертификат, а первый найденный каталог - как связка файлов закрытого ключа. Пароль от контейнера, если есть, передается первым параметром командной строки.

В каталоге `certificates/` содержатся различные комбинации тестового сертификата и закрытого ключа, с PIN кодом и без:

```
├── bundle-cert-only.zip          - только сертификат
├── bundle-cosign.zip             - сертификат + закрытый ключ БЕЗ пин-кода (для добавления второй подписи)
├── bundle-cyrillic.zip           - сертификат + закрытый ключ, название контейнера "тестовое название контейнера" (кириллица)
├── bundle-no-pin.zip             - сертификат + закрытый ключ БЕЗ пин-кода
├── bundle-pin.zip                - сертификат + закрытый ключ с пин-кодом 12345678
└── bundle-private-key-only.zip   - только закрытый ключ
```

Примеры:

```sh
# сертификат + закрытый ключ с пин-кодом
cat certificates/bundle-pin.zip | docker compose exec -T cryptopro /scripts/my 12345678

# сертификат + закрытый ключ БЕЗ пин-кода
cat certificates/bundle-no-pin.zip | docker compose exec -T cryptopro /scripts/my

# только сертификат
cat certificates/bundle-cert-only.zip | docker compose exec -T cryptopro /scripts/my

# только закрытый ключ
cat certificates/bundle-private-key-only.zip | docker compose exec -T cryptopro /scripts/my

# сертификат + закрытый ключ, название контейнера "тестовое название контейнера" (кириллица)
cat certificates/bundle-cyrillic.zip | docker compose exec -T cryptopro /scripts/my
```

![my-cert](./assets/my-cert.gif)

Более подробные инструкции:
- [Работа с КриптоПро на linux сервере](./docs/Работа%20с%20КриптоПро%20на%20linux%20сервере.pdf)

## Как скопировать подпись для production

Есть 2 варианта, безопасный и дешевый.

Безопасный:
- Купить отдельную ЭЦП
- Добавить пользователя, в Честном Знаке по подписи директор может добавить сотрудника и указать ему права доступа
- Выгрузить ее на сервер и использовать для подписания

Дешевый:
- Скопировать директорскую подпись, но придется повозиться с "защищенным" носителем типа рутокен. Не рекомендуется, тк при краже такой подписи хакер получает полный доступ к очень многим гос ресурсам от лица компании.

Более подробные инструкции:
- [Как скопировать контейнер с сертификатом на другой носитель](./docs/Как%20скопировать%20контейнер%20с сертификатом%20на другой%20носитель.pdf)
- [Копирование ЭЦП от ФНС на флешку (2024)](./docs/Копирование%20ЭЦП%20от%20ФНС%20на%20флешку%20(2024).pdf)

# CLI

## Просмотр установленных сертификатов

Сертификаты пользователя:

```sh
docker compose exec -T cryptopro certmgr -list
```

![show-certs](./assets/show-certs.gif)

Корневые сертификаты:

```sh
docker compose exec -T cryptopro certmgr -list -store root
```

## Подписание документа

Для примера установим этот тестовый сертификат:

```sh
# сертификат + закрытый ключ с пин-кодом
cat certificates/bundle-pin.zip | docker compose exec -T cryptopro /scripts/my 12345678
```

Его SHA1 Hash равен `dd45247ab9db600dca42cc36c1141262fa60e3fe` (узнать: `certmgr -list`), который будем использовать как указатель нужного сертификата.

Теперь передадим на `stdin` файл, в качестве команды - последовательность действий, и на `stdout` получим подписанный файл:

```sh
cat README.md | docker compose exec -T cryptopro sh -c 'tmp=`mktemp`; cat - > "$tmp"; cryptcp -sign -thumbprint dd45247ab9db600dca42cc36c1141262fa60e3fe -nochain -pin 12345678 "$tmp" "$tmp.sig" > /dev/null 2>&1; cat "$tmp.sig"; rm -f "$tmp" "$tmp.sig"'
```

Получилось довольно неудобно. Скрипт `scripts/sign` делает то же самое, теперь команда подписания будет выглядеть так:

```sh
cat README.md | docker compose exec -T cryptopro /scripts/sign dd45247ab9db600dca42cc36c1141262fa60e3fe 12345678
```

![sign](./assets/sign.gif)

Об ошибке можно узнать через стандартный `$?`.

## Проверка подписи

Подпишем файл из примера выше и сохраним его на диск:

```sh
cat README.md | docker compose exec -T cryptopro /scripts/sign dd45247ab9db600dca42cc36c1141262fa60e3fe 12345678 > certificates/README.md.sig
```

Тогда проверка подписанного файла будет выглядеть так:

```sh
cat certificates/README.md.sig | docker compose exec -T cryptopro sh -c 'tmp=`mktemp`; cat - > "$tmp"; cryptcp -verify -norev -f "$tmp" "$tmp"; rm -f "$tmp"'
```

То же самое, но с использованием скрипта:

```sh
cat certificates/README.md.sig | docker compose exec -T cryptopro /scripts/verify
```

![verify](./assets/verify.gif)

## Получение исходного файла из sig-файла

Возьмем файл из примера выше:

```sh
cat certificates/README.md.sig | docker compose exec -T cryptopro sh -c 'tmp=`mktemp`; cat - > "$tmp"; cryptcp -verify -nochain "$tmp" "$tmp.origin" > /dev/null 2>&1; cat "$tmp.origin"; rm -f "$tmp" "$tmp.origin"'
```

То же самое, но с использованием скрипта:

```sh
cat certificates/README.md.sig | docker compose exec -T cryptopro /scripts/unsign
```

![unsign](./assets/unsign.gif)

## Использование контейнера на удаленной машине

В примерах выше команды выглядят так: `cat ... | docker ...` или `curl ... | docker ...`, то есть контейнер запущен на локальной машине. Если же докер контейнер запущен на удаленной машине, то команды нужно отправлять через ssh клиент. Например, команда подписания:

```sh
cat README.md | ssh -q user@host 'docker compose exec -T cryptopro /scripts/sign dd45247ab9db600dca42cc36c1141262fa60e3fe 12345678'
```

Опция `-q` отключает приветствие из файла `/etc/banner` (хотя оно все равно пишется в `stderr`). А `/etc/motd` при выполнении команды по ssh не выводится.

В качестве эксперимента можно отправить по ssh на свою же машину так:

```sh
# копируем публичный ключ на "удаленную машину" (на самом деле - localhost)
ssh-copy-id $(whoami)@localhost
# пробуем подписать
cat README.md | ssh -q $(whoami)@localhost 'docker compose exec -T cryptopro /scripts/sign dd45247ab9db600dca42cc36c1141262fa60e3fe 12345678'
```

# Работа с контейнером через HTTP REST-сервер<a name="http"></a>

Установка сертификатов осуществляется через командую строку. Все остальные действия доступны по HTTP.

* `/certificates` - все установленные сертификаты пользователя (`GET`)
* `/certificate/root` - установка корневых сертификатов (`POST`)
* `/certificate/private_key` - установка приватного колюча (`POST`)
* `/license?serial_number=` - установка серийной лицензии (`POST`)
* `/signer` - подписание документов (`POST`)
* `/verify` - проверка подписанного документа (`POST`)
* `/unsigner` - получение исходного файла без подписей (`POST`)

![rest](https://raw.githubusercontent.com/dbfun/cryptopro/master/assets/rest.gif)

## Формат данных

Возвращаются данные в формате `JSON`.

## Обработка ошибок

Успешные действия возвращают код `200` и `"status": "ok"`.

Действия с ошибками возвращают `4xx` и `5xx` коды и `"status": "fail"`, в полях `errMsg` содержится описание ошибки, в `errCode` - ее код.

Например, обращение с неправильным методом

```sh
curl -sS -X POST --data-binary "bindata" http://localhost:8095/healthchecks
```

выведет такую ошибку:

```JSON
{"status":"fail","errMsg":"Method must be one of: GET","errCode":405}
```

## `/certificates` - все установленные сертификаты пользователя

```sh
curl -X 'GET' \
  'http://localhost:8085/certificate' \
  -H 'accept: application/json'
```

Если сертификатов нет:

```JSON
{"status":"fail","errMsg":"No certificates in store 'My'","errCode":404}
```

Если сертификаты есть:

```JSON
{
  "data_certificates": {
    "certificate_1": {
      "privateKey": {
        "providerName": "Crypto-Pro GOST R 34.10-2012 KC1 CSP",
        "uniqueContainerName": "HDIMAGE\\\\eb5f6857.000\\D160",
        "containerName": "eb5f6857-a08a-4510-8a96-df2f75b6d65a"
      },
      "algorithm": {
        "name": "ГОСТ Р 34.10-2012 256 бит",
        "val": "1.2.643.7.1.1.1.1"
      },
      "valid": {
        "from": "23.08.2021 12:07:25",
        "to": "23.08.2022 12:17:25"
      },
      "issuer": {
        "CN": "Test",
        "O": "Test",
        "OU": "Test",
        "STREET": "Test",
        "L": "Москва",
        "C": "RU",
        "raw": "CN=Test, O=Test, OU=Test, STREET=Test, L=Москва, S=77 Москва, C=RU, INN=Test, OGRN=Test"
      },
      "subject": {
        "E": "Test@Test.ru",
        "C": "RU",
        "L": "г Москва",
        "O": "Test",
        "CN": "Test",
        "STREET": "Test",
        "G": "Test",
        "SN": "Test ",
        "raw": "SNILS=Test, OGRN=Test, INN=Test, E=Test@Test.ru, C=RU, S=77 г. Москва, L=г Москва, O=Test, CN=Test, STREET=Test, T=Test, G=Test, SN=Test"
      },
      "thumbprint": "982AA9E713A2F99B10DAA07DCDC94A4BC32A1027",
      "serialNumber": "120032C3567443029CC358FCDF00000032C356",
      "hasPrivateKey": true
    }
  }
}
```

## `/certificate/root` - установка корневых сертификатов

Для установки коневых сертификатов нужно передать файл (с расширением cer или p7b) в сервис.

```sh
curl -X 'POST' \
  'http://localhost:8085/certificate/root' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@filename.p7b;type=application/x-pkcs7-certificates'
```

## `/certificate/private_key` - установка приватного колюча

Для установки приватного колюча нужно передать архив в сервис.
В каталоге `certificates/` содержатся различные комбинации тестового сертификата и закрытого ключа, с PIN кодом и без:

```
├── bundle-cert-only.zip          - только сертификат
├── bundle-cosign.zip             - сертификат + закрытый ключ БЕЗ пин-кода (для добавления второй подписи)
├── bundle-cyrillic.zip           - сертификат + закрытый ключ, название контейнера "тестовое название контейнера" (кириллица)
├── bundle-no-pin.zip             - сертификат + закрытый ключ БЕЗ пин-кода
├── bundle-pin.zip                - сертификат + закрытый ключ с пин-кодом 12345678
└── bundle-private-key-only.zip   - только закрытый ключ
```

С пин-кодом:
```sh
curl -X 'POST' \
  'http://localhost:8085/certificate/private_key?pin=1234' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@bundle-pin.zip;type=application/zip'
```

Без пин-кодом:
```sh
curl -X 'POST' \
  'http://localhost:8085/certificate/private_key' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@bundle-no-pin.zip;type=application/zip'
```
## `/license?serial_number=` - установка серийной лицензии

Для установки серийного номера лицензии нужно передать номер.

```sh
curl -X 'POST' \
  'http://localhost:8085/license?serial_number=12345-12345-12345-12345-12345' \
  -H 'accept: application/json' \
  -d ''
```

## `/signer` - подписание документов

Для подписания нужно передать файл в сервис.

С пин-кодом:
```sh
curl -X 'POST' \
  'http://localhost:8085/signer?pin=123' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@filename.pdf;type=application/pdf'
```

Без пин-кода:
```sh
curl -X 'POST' \
  'http://localhost:8085/signer' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@filename.pdf;type=application/pdf'
```

Вернется `JSON` - документ, в `signedContent` будет содержаться подписанный файл и в `filename` новое имя файла.

## `/verify` - проверка подписанного документа

Для проверки подписи передаем подписанный и не подписанный файлы.

```sh
curl -X 'POST' \
  'http://localhost:8085/verify' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'original_file=@filename1.pdf;type=application/pdf' \
  -F 'signed_file=@filename2.pdf;type=application/pdf'
```

Если файл прошел проверку, вернется список подписантов `signers`.


## `/unsigner` - получение исходного файла без подписей

Исходный файл вернется в поле `content`.

```sh
curl -X 'POST' \
  'http://localhost:8085/unsigner' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@filename.sig;type=application/sig'
```

## Пояснения к созданию образа

Скачать с официального сайта в `dist/` (необходимо быть залогиненым в системе):

* [КриптоПро CSP 5.0 для Linux (x64, deb)](https://www.cryptopro.ru/products/csp/downloads) => `dist/linux-amd64_deb.tgz`
* КриптоПро ЭЦП SDK [версия 2.0 для пользователей](https://cryptopro.ru/products/cades/downloads) => `dist/cades-linux-amd64.tar.gz` - Linux версию
* [Архив с исходниками](https://cryptopro.ru/sites/default/files/products/cades/pycades/pycades.zip) => `dist/pycades.zip`

Запустить:

```
docker build --tag cryptopro_5 .
```

### Возможные проблемы

В `Dockerfile` содержатся названия пакетов, например `lsb-cprocsp-devel_5.0.12000-6_all.deb`, которые могут заменить новой версией. Следует поправить названия пакетов в `Dockerfile`.

### Запуск контейнера

Запустим контейнер под именем `cryptopro`, к которому будем обращаться в примерах:

```sh
docker run -it --rm -p 8095:80 --name cryptopro cryptopro_5
```

Для сохранения сертификатов и лицензии дополнительно монтируем директории

```sh
docker run -it -p 8095:80 -v ./cryptopro-data:/var/opt/cprocsp/ -v ./cryptopro-etc:/etc/opt/cprocsp/ --name cryptopro cryptopro_5
```

# Настройка Крипто Про на MacOS

1. Установить браузер с поддрежкой ГОСТ сертификатов, рекомендую Яндекс Браузер
2. Автоматизировать настройку через сайт [Контур Диагностика](https://help.kontur.ru/uc), нужно выбрать раздел "для ЭТП и госпорталов". Так же можно убрать галочки с установки компонентов Контура
3. В браузере кликнуть на иконку расширения Крипто Про и выбрать "Проверить настройки плагина"
4.

# Ссылки

* [Страница расширения для Python](https://docs.cryptopro.ru/cades/pycades)
* [Инструкция по установке и сборке расширения для языка Python](https://docs.cryptopro.ru/cades/pycades/pycades-build)
* [Тестовый УЦ](http://testca2012.cryptopro.ru/ui/), его сертификаты: [корневой](http://testca2012.cryptopro.ru/cert/rootca.cer), [промежуточный](http://testca2012.cryptopro.ru/cert/subca.cer)


# Аналоги

Существует аналогичный пакет:
* [PHP CryptoPro Service (docker) with HTTP API](https://github.com/smskin/docker-cryptopro), идеальный вариант с PHP расширением;
* [cryptopro](https://github.com/dbfun/cryptopro), хороший вариант с PHP расширением и HTTP REST-сервером;
* [CryptoProCSP](https://github.com/taigasys/CryptoProCSP), он классный, но:
  * давно не обновлялся, используется версия `PHP5.6`
  * для запуска пришлось подредактировать `Dockerfile`
