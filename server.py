
from jinja2 import StrictUndefined
from flask import Flask, jsonify, render_template, redirect, request, flash, session
from model import connect_to_db, db, User, BucketList, PublicItem, PrivateItem, Journal, Friend
from flask_debugtoolbar import DebugToolbarExtension
from datetime import datetime
import facebook
import os
import requests
import json
import bcrypt

app = Flask(__name__)
app.secret_key = "ABC"
app.jinja_env.undefined = StrictUndefined

gm_api_key = os.environ['GOOGLE_MAPS_API_KEY']
travel_payouts_api = os.environ['TRAVEL_PAYOUTS_API']

@app.route('/')
def display_homepage():
    """Homepage"""

    public_items = PublicItem.query.all()
    email = session.get("email")
    lists = BucketList.query.filter(BucketList.email==email).all()

    return render_template("homepage.html", 
                           public_items=public_items,
                           lists=lists,
                           email=email)

# @app.route('/public/<pub_item_id>')
# def display_public_item_details(pub_item_id):
#     """Displays info about a public item."""

#     email = session.get("email")
#     username = session.get("username")
#     lists = BucketList.query.filter(BucketList.email==email).all()
#     item_info = PublicItem.query.filter(PublicItem.id==pub_item_id).one()
#     return render_template('public-item.html', 
#                            item_info=item_info,
#                            lists=lists,
#                            email=email,
#                            username=username,
#                            public_item_id=pub_item_id)

@app.route('/<list_id>/<priv_item_id>')
def display_private_item_details(list_id, priv_item_id):
    """Displays info about a private item."""

    item_info = PrivateItem.query.filter(PrivateItem.id==priv_item_id).one()
    return render_template('private-item.html', 
                           item_info=item_info)

@app.route('/search')
def process_search_form():
    """Processes a search form."""

    form_input = request.args.get('public-search')
    keywords = form_input.split()
    matched_items = []
    email = session.get('email')
    lists = BucketList.query.filter(BucketList.email==email).all()

    for word in keywords:
        items = PublicItem.query.filter(PublicItem.title.like("%{}%".format(word))).all()
        for item_object in items:
            matched_items.append(item_object)

    return render_template('search-results.html', 
                            matched_items=matched_items,
                            email=email,
                            lists=lists)

@app.route('/map')
def display_google_map():
    """Display markers on a map for all public items"""

    items = PublicItem.query.all()
    places = []

    for item in items:
        item_coordinates = [item.title, item.latitude,
                            item.longitude]
        places.append(item_coordinates)
    
    # change back to UTF-8
    for location in places:
        location[0] = str(location[0])

    return render_template("public-items-map.html",
                           gm_api_key=gm_api_key,
                           places=places)

@app.route('/flight-search')
def display_flight_form():

    return render_template("flight-search.html")

@app.route('/flight-results')
def display_flight_results():

    origin = request.args.get('origin')
    destination = request.args.get('destination')
    depart_date = request.args.get('depart-at')
    return_date = request.args.get('return-at')
    time = datetime.now()
    year = time.year

    url = ("http://api.travelpayouts.com/v1/prices/cheap?origin={}"
                "&depart_date={}-{}&currency=USD&token={}").format(origin,
                                                                   year,
                                                                   depart_date,
                                                                   travel_payouts_api)
    if destination != "-":
        url += "&destination={}".format(destination)

    if return_date != "":
        url += "&return_date={}-{}".format(year, return_date)

    print url
    r = requests.get(url)
    data = r.text
    flight_results = json.loads(data)

    flights = []

    for airport in flight_results['data']:
        number = str(flight_results['data'][airport].keys()[0])
        price = str(flight_results['data'][airport][number]['price'])
        return_at = str(flight_results['data'][airport][number]['return_at'])
        # TODO: Clean up variable names
        return_at = return_at.replace("T", " ").replace("Z", "")
        return_at = datetime.strptime(return_at, "%Y-%m-%d %H:%M:%S")
        return_at = return_at.strftime("%A, %B %d, %Y, %I:%M %p")
        departure_at = str(flight_results['data'][airport][number]['departure_at'])
        departure_at = departure_at.replace("T", " ").replace("Z", "")
        departure_at = datetime.strptime(departure_at, "%Y-%m-%d %H:%M:%S")
        departure_at = departure_at.strftime("%A, %B %d, %Y, %I:%M %p")
        airline = str(flight_results['data'][airport][number]['airline'])
        flight_number = str(flight_results['data'][airport][number]['flight_number'])

        flights.append([airport, price, return_at, departure_at, airline, flight_number])

    return render_template('flight-results.html', flights=flights)


@app.route('/register', methods=['GET','POST'])
def process_registation_form():
    """Display and process registration form"""

    if request.method == 'GET':
        return render_template('registration-form.html')

    username = request.form.get('username')
    email = request.form.get('email')
    first_name = request.form.get('first-name')
    last_name = request.form.get('last-name')
    password = request.form.get('password')
    # hashed_pw = bcrypt.hashpw(password.encode("UTF_8"),bcrypt.gensalt())
    email_query = User.query.filter(User.email==email).all()

    if email_query:
        flash("An account for {} already exists!".format(email))
        return redirect("/login")
    else:
        user = User(email=email, password=password, first_name=first_name,
                    last_name=last_name, username=username)
        db.session.add(user)
        db.session.commit()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def process_login_info():
    """Checks if user email and password exist on same account, then logs in or redirects."""

    # Haslib

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    password = request.form.get("password")
    

    user_query = User.query.filter(User.email==email).first()
    if user_query and user_query.password == password:
        session["email"] = user_query.email
        flash("You have successfully logged in!")
        return redirect("/my-lists")
    else:
        flash("Email or Password is incorrect. Please try again!")
        return redirect("/login")

@app.route('/logout')
def log_user_out():
    """Logs a user out."""

    del session['username']
    del session['email']
    del session['token']
    public_items = PublicItem.query.all()
    flash("You have successfully logged out!")
    return redirect("/")

@app.route('/facebook', methods=['POST'])
def check_for_user():
    """Checks database for user with facebook email"""

    facebook_id = request.form.get('id')
    name = request.form.get('name')
    email = request.form.get('email')
    token = request.form.get('token')
    session['token'] = token
    first_name = name.split()[0]
    last_name = name.split()[1]

    print first_name
    print last_name
    print email
    
    user_query = User.query.filter(User.email==email).first()

    if user_query:
        return "user exists"
    else:
        # pop up window asking for password
        # add user to database
        print "need email"
        return "need email"

@app.route('/facebook/login', methods=['POST'])
def login_user():

    new = request.form.get('new')
    print "in Facebook login"


    print "New: " + new
    # if new user
    if new == "true":
        print "Got to new user"
        email = request.form.get('email')
        password = request.form.get('id')
        print password
        username = request.form.get('username')
        name = request.form.get('name')
        first_name, last_name = name.split()
        # Get profile picture
        token = session['token']
        picture_url = 'https://graph.facebook.com/v2.8/me/picture?type=large&access_token={}'.format(token)
        r = requests.get(picture_url)
        picture = str(r.url)

        user = User(email=email, password=password, first_name=first_name,
                    last_name=last_name, username=username, facebook_id=password,
                    profile_picture=picture)
        db.session.add(user)
        db.session.commit()

    # If user exists
    else:
        email = request.form.get('email')
        username = request.form.get('username')
        user = User.query.filter(User.email==email).first()
        print "Find user"

    session["username"] = username
    session["email"] = email

    # Get Facebook friend ids
    token = session['token']
    url = 'https://graph.facebook.com/v2.8/me?fields=id%2Cname%2Cfriends%7Bid%2Cname%7D&access_token={}'.format(token)
    r = requests.get(url)
    results = json.loads(r.text)

    friends = []
    for friend in results['friends']['data']:
        facebook_id = str(friend['id'])
        friends.append(facebook_id)

    for facebook_id in friends:
        # Find friend's user information
        fb_friend = User.query.filter(User.facebook_id==facebook_id).first()
        print fb_friend
        # If it finds it, get the email
        if fb_friend:
            friend_email = fb_friend.email
            email = request.form.get('email')
            friend_query = Friend.query.filter(Friend.user==email, Friend.fb_friend==friend_email).first()
            if not friend_query:
                friendship = Friend(user=email, fb_friend=friend_email)
                db.session.add(friendship)
    db.session.commit()

    return redirect('/')

@app.route('/profile/<facebook_id>')
def display_profile(facebook_id):
    """Displays a user's profile page"""
    user = User.query.filter(User.facebook_id==facebook_id).one()
    email = session['email']
    user_bucket_lists = BucketList.query.filter(BucketList.email==email).all()
    private_items = (db.session.query(PrivateItem).join(BucketList).join(User)
                    .filter(User.email==user.email).all())
    return render_template('profile.html',
                            user=user,
                            private_items=private_items,
                            email=email,
                            lists=user_bucket_lists)

@app.route('/facebook/friends')
def display_fb_friends():
    """Displays a user's facebook friends."""
    email = session['email']
    user = User.query.get(email)
    # list of user objects for friends
    friends = user.followers
    token = session['token']

    return render_template("facebook-friends.html",
                            friends=friends)

@app.route('/facebook/post')
def post_completed_bucket_item():
    """Post to Facebook about completed bucket item"""
    token = session['token']
    graph = facebook.GraphAPI(access_token=token, version='2.8')

    # attachment =  {
    # 'name': 'Link name'
    # 'link': 'https://www.example.com/',
    # 'caption': 'Check out this example',
    # 'description': 'This is a longer description of the attachment',
    # 'picture': 'https://www.example.com/thumbnail.jpg'
    # }

    graph.put_wall_post(message='Check this out...', attachment=attachment)
    return "Wall post successful"

@app.route('/my-lists')
def display_bucket_lists():
    """Display users bucket lists."""

    email = str(session.get("email"))
    user_bucket_lists = BucketList.query.filter(BucketList.email==email).all()

    if email:
        user = User.query.get(email)
        progress_results = user.get_progress()

        items = progress_results['total_items']
        checked_off_items = progress_results['checked_items']

        return render_template("user-lists.html", 
                            user_bucket_lists=user_bucket_lists,
                            items=items,
                            checked_off_items=checked_off_items)
    else:
        flash("You are not signed in")
        return redirect('/login')

@app.route('/progress.json')
def get_progress_of_all_items():
     email = str(session.get("email"))
     if email:
        user = User.query.get(email)
        progress_results = user.get_progress()

        return jsonify(progress_results)



@app.route('/my-lists/add-form')
def display_add_list_form():
    """Display form to add new bucket list."""

    return render_template("add-list.html")


@app.route('/my-lists/add', methods=['POST'])
def add_bucket_list():
    """Add new bucket list."""

    title = request.form.get('title')
    email = request.form.get('email')

    user_list = BucketList.query.filter(BucketList.email==email,
                                        BucketList.title==title).first()
    if not user_list:
        title = request.form.get('title')
        email = request.form.get('email')
        new_list = BucketList(email=email, title=title)
        db.session.add(new_list)
        db.session.commit()
        flash("Your list has been created!")
        return redirect('/my-lists')

    flash("You already have a list named {}".format(title))
    return redirect('/my-lists/add')

@app.route('/delete-item', methods=['POST'])
def delete_priv_item():
    """Deletes an item from a user's bucket list."""

    del_item = request.form.get('delete-item')
    item_id = request.form.get('item-id')
    print del_item

    if del_item == 'delete':
        item = PrivateItem.query.filter(PrivateItem.id==item_id).one()
        db.session.delete(item)
        db.session.commit()

    return redirect('/')


# Id of list object instead of title
@app.route('/my-lists/<list_id>')
def display_bucket_list(list_id):
    """Displays a user's bucket list."""

    bucket_list = BucketList.query.filter(BucketList.id==list_id).first()
    b_list_id = list_id

    places = []

    print bucket_list
    print bucket_list.priv_items
    for item in bucket_list.priv_items:
        item_coordinates = [item.public_item.title, item.public_item.latitude,
                            item.public_item.longitude]
        places.append(item_coordinates)
    
    # change back to UTF-8
    for location in places:
        location[0] = str(location[0])

    all_list_items = PrivateItem.query.filter(PrivateItem.list_id==b_list_id).count()
    checked_off_items = PrivateItem.query.filter(PrivateItem.list_id==b_list_id, PrivateItem.checked_off==True).count()
    progress = str(checked_off_items) + "/" + str(all_list_items)

    return render_template("bucket-list.html", 
                           bucket_list=bucket_list,
                           b_list=b_list_id,
                           gm_api_key=gm_api_key,
                           places=places,
                           progress=progress)

@app.route('/add-item-form', methods=['GET', 'POST'])
def display_add_item_form():
    """Displays bucket item form."""

    email = session["email"]

    lists = BucketList.query.filter(BucketList.email==email).all()
    print(email, lists)
    return render_template("add-item-form.html",
                           lists=lists,
                           gm_api_key=gm_api_key)
    

@app.route('/add-item/public', methods=['POST'])
def add_item_from_public():
    email = session['email']
    public_id = request.form.get('id')
    list_title = request.form.get('title')
    print list_title
    bucket_list = BucketList.query.filter(BucketList.title==list_title,
                                          BucketList.email==email).first()
    bucket_list_id = bucket_list.id
    print "About to print list_id"
    print bucket_list_id
    tour_link = None
    private_item = create_private_item(public_id, bucket_list_id, tour_link)
    print private_item
    return "Item added"


@app.route('/add-item/process', methods=['POST'])
def process_add_bucket_item():
    """Checks if item already exists in a list, if not then adds it."""

    title = request.form.get('title')
    tour_link = request.form.get('tour-link')
    image = request.form.get('image')
    description = request.form.get('description')
    list_title = request.form.get('list')
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    print latitude
    print longitude

    # Query for the public item with the title as the input title
    item = PublicItem.query.filter(PublicItem.title.ilike(title)).first()

    # If there is not a public item with that title, create a public and private item    
    if not item:
        item = PublicItem(title=title,image=image,description=description,
                                  latitude=latitude, longitude=longitude)
        db.session.add(item)
        db.session.commit()
    public_id = item.id
    b_list = BucketList.query.filter(BucketList.title==list_title).first()
    b_list_id = b_list.id
    create_private_item(public_id, b_list_id, tour_link)
    return redirect('/my-lists/{}'.format(b_list_id))



def create_private_item(public_id, list_id, tour_link):
    email = session['email']
    print public_id
    print list_id
    print email
    user = User.query.filter(User.email==email).one()
    print user
    print user.email
    # Check if a private item for that user exists with that title
    private_item = (db.session.query(PrivateItem).join(BucketList).join(User)
                    .filter(PrivateItem.public_item_id==public_id, 
                            User.email==email).first())

    # If there is a private item with that title
    if private_item:
        flash("You already have an item with that title!")
        return redirect('/my-lists')

    new_item = PrivateItem(public_item_id=public_id,
                           list_id=list_id,
                           tour_link=tour_link)
    db.session.add(new_item)
    db.session.commit()
    flash("Your item has been added!")



@app.route('/check-off-item', methods=['POST'])
def check_off_item():
    """Changes the status of the item as completed."""

    item_id = request.form.get("item-id")
    list_id = request.form.get("list-id")

    item = PrivateItem.query.filter(PrivateItem.id==item_id).first()
    item.checked_off = True
    db.session.commit()

    return redirect('/{}/{}'.format(list_id,item_id))


if __name__ == "__main__":

    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)
    
    app.run(port=5000, host='0.0.0.0')