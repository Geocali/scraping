# -*- coding: latin-1 -*-

import sys
if (sys.version_info[0] == 3):
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

from lxml import etree

import pandas as pd
import time
import numpy as np
import datetime
import sqlite3

# =============== on récupère tous les résumés de toutes les annonces
def toutes_annonces(mot_cle):
    htmlparser = etree.HTMLParser()
    page = 1
    ok1 = True
    results = []
    page_existe = True
    while (ok1 and page_existe == True): # and page <= 1):

        try:
            url_request = "https://www.leboncoin.fr/locations/offres/ile_de_france/?o=" + str(page) + "&q=" + mot_cle + "&it=1&location=Paris" # !!!!!!!!!!!!!!!!!
            #url_request = 'file:///C:/data_cv/prog/caves/cave_general.htm' # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

            #url_request = 'file:///cave_general.htm' # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            page_ads = urlopen(url_request)
            tree_ads = etree.parse(page_ads, htmlparser)

            # on vérifie que la page contient des résultats
            # page_existe = (tree_ads.findtext("result_ad_not_found_proaccount") == None)
            # print(page_existe)
            try:
                xpath = "//*[@id=\"result_ad_not_found_proaccount\"]"
                iop = tree_ads.xpath(xpath)
                page_existe = len(iop) == 0
            except:
                page_existe = True

            if (page_existe == True):
                # on va lister toutes les résumés d'annonce de la page dans un tableau
                i = 1
                ok2 = True
                while (ok2):
                    try:

                        ad_glob = tree_ads.xpath("/html/body/section[1]/main/section/section/section/section/ul/li[" + str(i) + "]/a")

                        ad_id = ad_glob[0].values()[0].split("/")[-1].split(".")[0]

                        ad_url = ad_glob[0].values()[0] #"http:" + ad_glob[0].values()[0]

                        ad_title = ad_glob[0].values()[1]

                        #ad_type_elmt = tree_ads.xpath("/html/body/section[1]/main/section/section/section/section/ul/li[" + str(i) + "]/a/section/p[1]")
                        #ad_type = ad_type_elmt[0].getchildren()[0].values()
                        #print(ad_type)
                        ad_type = ""

                        ad_city_elmt = tree_ads.xpath("/html/body/section[1]/main/section/section/section/section/ul/li[" + str(i) + "]/a/section/p[2]")
                        ad_city = ad_city_elmt[0].getchildren()[0].values()[1]

                        ad_price_elmt = tree_ads.xpath("/html/body/section[1]/main/section/section/section/section/ul/li[" + str(i) + "]/a/section/h3")
                        ad_price = int(ad_price_elmt[0].values()[2])

                        ad_time_elmt = tree_ads.xpath("/html/body/section[1]/main/section/section/section/section/ul/li[" + str(i) + "]/a/section/aside/p")
                        ad_time = ad_time_elmt[0].values()[2]

                        result = pd.DataFrame([ad_id, ad_title, ad_price, ad_url, ad_time, ad_city, ad_type], index=['id', 'title', 'price', 'url', 'time', 'city', 'type']).transpose()
                        print(ad_title)
                        results.append(result)
                        i = i + 1
                    except:
                        ok2 = False
                print("page " + str(page))
                time.sleep(1)
                page = page + 1
        except:
            ok1 = False
            print(sys.exc_info()[0])
        print(ok1, page_existe)

    df_resumes = pd.concat(results)
    df_resumes = df_resumes.set_index('id', drop=False)
    df_resumes = df_resumes.convert_objects(convert_numeric=True)
    #df_resumes = pd.to_numeric(df_resumes)

    return df_resumes


# ================ pour une page, enregistrer la surface et la description

def infos_annonce(url_request):
    htmlparser = etree.HTMLParser()
    page_ads = urlopen(url_request)
    tree_ads = etree.parse(page_ads, htmlparser)
    ad_title = tree_ads.xpath("/html/body/section[1]/main/section/section/section/header/h1")[0].text

    results = []
    for i_section in range(1, 3):
        for i_div in range(1, 15):
            xpath_category_i = "/html/body/section[1]/main/section/section/section/section/section[" + str(i_section) + "]/div[" + str(i_div) + "]/h2/span[" + str(1) + "]"
            xpath_value_i = "/html/body/section[1]/main/section/section/section/section/section[" + str(i_section) + "]/div[" + str(i_div) + "]/h2/span[" + str(2) + "]"
            try:
                category_i = tree_ads.xpath(xpath_category_i)[0].text.replace("\\n", "")
                value_i = tree_ads.xpath(xpath_value_i)[0].text
            except:
                category_i = ''
                value_i = ''
            if(len(category_i) != 0):
                results.append([i_section, i_div, category_i, value_i])
    
    # on cherche les informations qui nous intéressent
    # la surface
    category = "Surface"
    result = ""
    for line in results:
        if(line[2].find(category) > -1):
            result = line[3]
    if(len(result) > 0):
        result = result.split(" ")[0]
    if(len(result)>0):
        ad_surface = int(result)
    else:
        ad_surface = 0

    # le nombre de pièces
    category = "Pièces".decode('utf8')
    result = ""
    for line in results:
        text = line[2]#.decode('latin1')
        if(text.find(category) > -1):
            result = line[3]
    if(len(result) > 0):
        result = result.split(" ")[0]
    if(len(result)>0):
        pieces = int(result)
    else:
        pieces = 0

    # pour ne pas garder les appartements
    if(pieces > 1):
        ad_surface = np.nan

    # on récupère la description
    ad_description = ""
    for section_i in range(1, 3):
        for div_i in range(10, 15):
            #xpath1 = "//*[@id=\"adview\"]/section/section/section/div[12]/p[2]/text()[" + str(i) + "]"
            xpath = "/html/body/section[1]/main/section/section/section/section/section[" + str(section_i) + "]/div[" + str(div_i) + "]/p[2]/text()"
            #tmp = tree_ads.xpath(xpath1)[0].replace("\\n", "")
            #ad_description = ad_description + "<br>" + tmp
            try:
                obj = tree_ads.xpath(xpath)
                for i in range(len(obj)):
                    ad_description = ad_description + "<br>" + obj[i].replace("\\n", "")
            except:
                print("description not found")
    ad_description = ad_description[4:]

    # on récupère la date de création de l'annonce
    xpath = "//*[@id=\"adview\"]/section/section/section/p"
    ad_creation = tree_ads.xpath(xpath)[0].values()[2]

    # on cherche des mots clés pour voir s'il s'agit d'un appartement
    # si c'est le cas, on fixe la surface à 0 pour ne pas le prendre en compte
    keywords = ['Appart', 'appart', 'studio', 'Studio', 'meublé'.decode('utf8')]
    for keyword in keywords:
        if ad_title.find(keyword) != -1:
            ad_surface = np.nan


    print("surface : " + str(ad_surface))
    return ad_surface, ad_description, ad_creation
                    

#df_details = pd.read_csv('details_caves.csv', sep=";", encoding='latin1')
conn = sqlite3.connect('caves.db')
query = "SELECT * FROM caves ORDER BY date_creation"
df_details = pd.read_sql_query(query,conn, parse_dates=['date_creation', 'date_suppression'])

# ============= Pour toutes les annonces dont on n'a pas le détail, on va les enregistrer
# on fait la liste des id qu'on a déjà :
ids = df_details['id'].tolist()

# on récupère toutes les annonces présentes sur le site leboncoin.fr
df_resumes = toutes_annonces("cave")

# on enregistre les informations de mesure dans la table "mesures" de la base de données
df_mesures = df_resumes[['url', 'id']]
t = str(datetime.datetime.now())
df_mesures['date_mesure'] = [t for i in range(df_mesures.shape[0])]
df_mesures.to_sql("mesures", conn, if_exists='append', index=False)

# on fait la liste des annonces présentes sur leboncoin.fr, mais pas dans la base de données
df_missing = df_resumes[~df_resumes.id.isin(ids)]

# on ouvre chacune de ces annonces non connues pour enregistrer la surface et la description
ad = 1
df_adding = pd.DataFrame()
for index, row in df_missing.iterrows():
    if(ad<500):
        print(" ==== annonce " + str(ad) + " ====")

        ad_surface, ad_description, ad_creation = infos_annonce("http:" + row['url']) # !!!!!!!!!!!!!!!!!!!!!!!!!!!
        #ad_surface, ad_description, ad_creation = "3", "cave de ouf", "2017-10-12" # !!!!!!!!!!!!!!!!!!!!!!!!!!!!

        df_adding = df_adding.append({'id':row['id'], 'title':row['title'], 'price':row['price'], 'url':row['url'], 'type':row['type'], 'city':row['city'], 'surface':ad_surface, 'description':ad_description, 'date_creation':ad_creation, 'date_suppression':np.nan}, ignore_index=True)

        time.sleep(1)
    ad = ad + 1

# on ajoute les nouvelles annonces à la base de données
df_adding.to_sql("caves", conn, if_exists='append', index=False)

# on ferme la base de données
conn.close()



# ============= On cherche les annonces qui ont disparu
# masque sur les annonces qui ont disparu par rapport à la liste de toutes les annonces
#mask_disparues = ~df_details.id.isin(df_resumes['id'].tolist())
# masque sur les annonces qui n'ont pas déjà disparu
#mask_deja_disparue = pd.isnull(df_details['date_suppression'])
#mask = mask_disparues & mask_deja_disparue

# pour les annonces qui viennent de disparaitre, on enregistre la date du jour
#df_details.loc[mask, 'date_suppression'] = str(datetime.date.today())

# on enregistre
#df_details.to_csv('details_caves.csv', sep=";", index=None, encoding='latin1')
