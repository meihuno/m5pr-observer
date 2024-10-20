# import
import os
import datetime
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods import media
from wordpress_xmlrpc.methods.users import GetUserInfo
from wordpress_xmlrpc.methods.posts import GetPost, GetPosts, NewPost, EditPost
# from wordpress_xmlrpc.methods.pages import GetPage, GetPageStatusList
import pprint as pp

class EditWordPress(object):

    def __init__(self):
        # Set URL, ID, Password
        self.WORDPRESS_ID = os.getenv('WORDPRESS_USERNAME')
        self.WORDPRESS_PW = os.getenv('WORDPRESS_PASSWORD')
        self.WORDPRESS_URL = "http://m5pr-observer.com/xmlrpc.php"
        self.target_page_title = 'Top Page'
        # if post.title == 'WordPress練習ページ':

    def gogo_edit_page(self, body="<p>This is a blank page.</p>"):

        wp = Client(self.WORDPRESS_URL, self.WORDPRESS_ID, self.WORDPRESS_PW)
        user_info = wp.call(GetUserInfo())
        print(user_info)
        posts = wp.call(GetPosts({'post_type': 'page'}))
        
        for post in posts:
            content = post.content
            if post.title == self.target_page_title:
                # pp.pprint([post.thumbnail, post.terms])
                print(post.id)
                # attachment_id = post.thumbnail['attachment_id']
                post.thumbnail = post.thumbnail['attachment_id']
                post.content = body
                
                wp.call(EditPost(post.id, post))

    def show_page_content(self, body="<p>This is a blank page.</p>"):

        wp = Client(self.WORDPRESS_URL, self.WORDPRESS_ID, self.WORDPRESS_PW)
        user_info = wp.call(GetUserInfo())
        print(user_info)
        posts = wp.call(GetPosts({'post_type': 'page'}))
        
        for post in posts:
            content = post.content
            if post.title == self.target_page_title:
                # pp.pprint([post.thumbnail, post.terms])
                print(post.id)
                print(post.content)    # attachment_id = post.thumbnail['attachment_id']

if __name__=="__main__":
    box = EditWordPress()
    box.show_page_content()
