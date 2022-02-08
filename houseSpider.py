import json
import sys
import urllib

import scrapy
from imgcat import imgcat
from tabulate import tabulate


class HouseSpider(scrapy.Spider):
    name = "house_spider"
    start_urls = [
        "https://www.zoopla.co.uk/to-rent/property/derby/?added=7_days&beds_max=2&beds_min=2&page_size=25&price_frequency=per_month&view_type=list&q=Derby%2C%20Derbyshire&radius=0&results_sort=newest_listings&search_source=refine",
        "https://www.rightmove.co.uk/property-to-rent/find.html?locationIdentifier=REGION%5E418&maxBedrooms=2&minBedrooms=2&propertyTypes=&maxDaysSinceAdded=7&includeLetAgreed=false&mustHave=&dontShow=&furnishTypes=&keywords=",
    ]

    def parse(self, response):
        slot = response.meta["download_slot"]
        if "rightmove" in slot:
            return self.parseRightMove(response)
        elif "zoopla" in slot:
            return self.parseZoopla(response)
        else:
            print("ELSE", response)

    def parseRightMove(self, response):
        imgspace = "0" * 30
        site = response.meta["download_slot"]
        pre_items = response.xpath(
            './/div[contains(@class, "l-searchResult") and contains(@class, "is-list") and not(contains(@class, "is-hidden"))]'
        )

        items = []
        for pre_item in pre_items:
            if (
                pre_item.xpath(
                    './/div[contains(@class, "propertyCard") and contains(@class, "propertyCard--premium") and contains(@class, "propertyCard--featured")]'
                ).get()
                is None
            ):
                items.append(pre_item)

        print("RIGHT", "items:", len(items))

        rows = []
        imgs = []
        i = 1
        for item in items:
            added = item.xpath(
                './/span[contains(@class, "propertyCard-branchSummary-addedOrReduced")]/text()'
            ).extract_first()

            if item.xpath('.//a[@data-test="property-img"]//img/@src').get() is not None:
                imgdata = urllib.request.urlopen(
                    item.xpath('.//a[@data-test="property-img"]//img/@src').get()
                ).read()

                imgs.append(imgdata)
            else:
                imgs.append(b'0')

            row = []
            row.append(i)
            row.append(imgspace)
            row.append(
                item.xpath(
                    './/address[contains(@class, "propertyCard-address")]/span/text()'
                ).get()
            )

            row.append(
                item.xpath(
                    './/div[@class="propertyCard-details"]//h2[@class="propertyCard-title"]/text()'
                )
                .extract_first()
                .strip()
            )

            row.append(
                item.xpath(
                    './/span[@class="propertyCard-priceValue"]/text()'
                ).extract_first()
            )

            row.append(added)

            row.append(
                "https://"
                + site
                + item.xpath(
                    './/div[@class="propertyCard-details"]/a/@href'
                ).extract_first()
            )

            rows.append(row)

            i = i + 1

        self.printConsole(
            rows,
            [
                "#",
                "Image",
                "Address",
                "Description",
                "Price",
                "Added on",
                "Link",
            ],
            imgs,
            imgspace,
        )

        print(">" * 20)

        pass

    def parseZoopla(self, response):
        imgspace = "0" * 30
        site = response.meta["download_slot"]

        jsonobj = json.loads(
            response.xpath('.//script[@id="__NEXT_DATA__"]/text()').get().strip()
        )

        items = jsonobj["props"]["pageProps"]["initialProps"][
            "regularListingsFormatted"
        ]

        print("ZOO", "items:", len(items))
        rows = []
        imgs = []

        i = 1
        for item in items:
            if item["image"]["src"] is not None:
                imgdata = urllib.request.urlopen(item["image"]["src"]).read()
                imgs.append(imgdata)
            else:
                imgs.append(b'0')
            
            row = []
            row.append(i)
            row.append(imgspace)
            row.append(item["address"])
            row.append(item["title"])
            row.append(item["price"])
            row.append(
                item["publishedOn"]
                + "(available from: "
                + item["availableFrom"]
                + ")",
            )

            row.append("https://" + site + item["listingUris"]["detail"])
            rows.append(row)

            i = i + 1

        self.printConsole(
            rows,
            [
                "#",
                "Image",
                "Address",
                "Description",
                "Price",
                "Added on",
                "Link",
            ],
            imgs,
            imgspace,
        )

        pass

    def printConsole(self, rows, headers, imgs, imgspace):
        s = tabulate(rows, headers, tablefmt="pretty")
        bw = sys.stdout.buffer
        ix = 0
        for l in s.splitlines():
            if imgspace in l:
                ls = l.split(imgspace)
                bw.write(str.encode(ls[0]))
                imgcat(imgs[ix], height=10, width=30, fp=bw)
                bw.write(str.encode(ls[1]))
                bw.write(b"\n")
                bw.flush()
                ix = ix + 1
            else:
                bw.write(str.encode(l))
                bw.write(b"\n")
                bw.flush()
            # print('#', l)
        pass
