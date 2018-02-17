class SetStructure:
    def __init__(self, link, category):
        self.link = link
        self.category = category

    def display_details(self):
        print("The category of the product is:", self.category, " URL:", self.link)

    def get_link(self):
        return self.link

    def get_category(self):
        return self.category
