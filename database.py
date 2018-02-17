import rethinkdb as r
import json

def connect():
    r.connect("localhost", 28015).repl()


def create_amazon_table():
    r.table_create("amazon_products").run()


def insert(JSONobj):
    r.table("amazon_products").insert(JSONobj).run()

def construct_database_node(new,ratings,price_ascending,price_descending,category_name):
    node={category_name:{}}
    node[category_name]['new'] = new
    node[category_name]['ratings'] = ratings
    node[category_name]['price-ascending'] = price_ascending
    node[category_name]['price-descending'] = price_descending
    return json.dumps(node,indent=4)

def delete_database():
    r.table("amazon_products").delete().run()