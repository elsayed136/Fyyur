#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func

import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

import sys
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)


# TODO: connect to a local postgresql database

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(500))

    artist = db.relationship('Artist', secondary='shows')
    genres = db.relationship('VenueGenreList', backref='genres', lazy=True)

    def __repr__(self):
        return f'<Venue name: {self.name}'


class VenueGenreList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id))

    def __repr__(self):
        return self.name


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(500))

    venue = db.relationship('Venue', secondary='shows')

    genres = db.relationship('ArtistGenreList', backref='genres', lazy=True)

    def __repr__(self):
        return f'<Artist id: {self.id}, name: {self.name}'


class ArtistGenreList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id))

    def __repr__(self):
        return self.name


class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey(Venue.id))
    artist_id = db.Column(db.Integer, db.ForeignKey(Artist.id))
    start_time = db.Column(db.DateTime)

    venue = db.relationship('Venue', backref='venues', lazy=True)

    artist = db.relationship('Artist', backref='artists', lazy=True)

    def __repr__(self):
        return f'<Show id: {self.id}, venue_id: {self.venue_id}, artist_id: {self.artist_id}, start_time: {self.start_time}'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


def is_upcoming(date):
    curr_date = datetime.datetime.now().date()
    if date.year >= curr_date.year and date.month > curr_date.month:
        return True
    else:
        return False

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    error = False
    body = []
    try:
        cities = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
        for c in cities:
            venue_list = []
            for venue in Venue.query.filter_by(city=c.city).all():
                dect = {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": Show.query.filter_by(venue_id=venue.id).count(),
                }
                venue_list.append(dect)
            obj = {
                "city": c.city,
                "state": c.state,
                "venues": venue_list,
            }
            body.append(obj)
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/venues.html', areas=body)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    error = False
    body = {}
    try:
        search_term = request.form.get('search_term')
        search = f"%{search_term}%"
        venues = Venue.query.filter(Venue.name.ilike(search)).all()

        body['count'] = len(venues)
        data = []
        for venue in venues:
            data.append({
                'id': venue.id,
                'name': venue.name,
                "num_upcoming_shows": 0,
            })
        body['data'] = data
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/search_venues.html', results=body, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    error = False
    body = {}
    try:
        venue = Venue.query.get(venue_id)
        body['id'] = venue.id
        body['name'] = venue.name
        body['genres'] = venue.genres
        body['address'] = venue.address
        body['city'] = venue.city
        body['state'] = venue.state
        body['phone'] = venue.phone
        body['website'] = venue.website
        body['facebook_link'] = venue.facebook_link
        body['seeking_talent'] = venue.seeking_talent
        body['image_link'] = venue.image_link

        past_shows = []
        upcoming_shows = []
        shows = Show.query.join(Venue, Venue.id == venue_id).all()
        for show in shows:
            if is_upcoming(show.start_time):
                upcoming_shows.append({
                    "artist_id": show.artist.id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": str(show.start_time)
                })
            else:
                past_shows.append({
                    "artist_id": show.artist.id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": str(show.start_time)
                })
        body['past_shows'] = past_shows
        body['upcoming_shows'] = upcoming_shows
        body['past_shows_count'] = len(past_shows)
        body['upcoming_shows_count'] = len(upcoming_shows)

    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/show_venue.html', venue=body)
#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    body = {}
    try:
        req = request.form
        name = req['name']
        city = req['city']
        state = req['state']
        address = req['address']
        phone = req['phone']
        genres = req.getlist('genres')
        facebook_link = req['facebook_link']
        genre_list = []

        venue = Venue(name=name, city=city, state=state, address=address, phone=phone, facebook_link=facebook_link)
        for g in genres:
            genre_list.append(VenueGenreList(name=g))

        venue.genres = genre_list
        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except():
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    error = False
    body = []
    try:
        artists = Artist.query.all()
        for artist in artists:
            body.append({
                "id": artist.id,
                "name": artist.name,
            })
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        pass
    if error:
        abort(500)
    else:
        return render_template('pages/artists.html', artists=body)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    error = False
    body = {}
    try:
        search_term = request.form.get('search_term')
        search = f"%{search_term}%"
        artists = Artist.query.filter(Artist.name.ilike(search)).all()

        body['count'] = len(artists)
        data = []
        for artist in artists:
            data.append({
                'id': artist.id,
                'name': artist.name,
                "num_upcoming_shows": 0,
            })
        body['data'] = data
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/search_artists.html', results=body, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    error = False
    body = {}
    try:
        artist = Artist.query.get(artist_id)
        body['id'] = artist.id
        body['name'] = artist.name
        body['genres'] = artist.genres
        body['city'] = artist.city
        body['state'] = artist.state
        body['phone'] = artist.phone
        body['seeking_venue'] = artist.seeking_venue
        body['image_link'] = artist.image_link

        past_shows = []
        upcoming_shows = []
        shows = Show.query.join(Artist, Artist.id == artist_id).all()
        for show in shows:
            if is_upcoming(show.start_time):
                upcoming_shows.append({
                    "venue_id": show.venue.id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": str(show.start_time)
                })
            else:
                past_shows.append({
                    "venue_id": show.venue.id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": str(show.start_time)
                })
        body['past_shows'] = past_shows
        body['upcoming_shows'] = upcoming_shows
        body['past_shows_count'] = len(past_shows)
        body['upcoming_shows_count'] = len(upcoming_shows)

    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/show_artist.html', artist=body)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False

    try:
        req = request.form
        artist = Artist.query.get(artist_id)

        artist.name = req['name']
        artist.city = req['city']
        artist.state = req['state']
        artist.phone = req['phone']
        artist.facebook_link = req['facebook_link']
        genres = req.getlist('genres')
        genre_list = []
        for genre in genres:
            genre_list.append(ArtistGenreList(name=genre))

        artist.genres = genre_list

        db.session.commit()
    except:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)

    form = VenueForm(obj=venue)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False

    try:
        req = request.form
        venue = Venue.query.get(venue_id)

        venue.name = req['name']
        venue.city = req['city']
        venue.state = req['state']
        venue.phone = req['phone']
        venue.address = req['address']
        venue.facebook_link = req['facebook_link']
        genres = req.getlist('genres')
        genre_list = []
        for genre in genres:
            genre_list.append(VenueGenreList(name=genre))

        venue.genres = genre_list

        db.session.commit()
    except:
        db.session.rollback()

        error = True
    finally:
        db.session.close()

    if error:
        abort(500)
    else:
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    body = {}
    try:
        req = request.form
        name = req['name']
        city = req['city']
        state = req['state']
        phone = req['phone']
        genres = req.getlist('genres')
        facebook_link = req['facebook_link']
        genre_list = []

        artist = Artist(name=name, city=city, state=state, phone=phone, facebook_link=facebook_link)

        for g in genres:
            genre_list.append(ArtistGenreList(name=g))

        artist.genres = genre_list
        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    error = False
    body = []
    try:
        shows = Show.query.all()
        for show in shows:
            body.append({
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'artist_id': show.artist.id,
                'artist_name': show.artist.name,
                'artist_image_link': show.artist.image_link,
                'start_time': format_datetime(str(show.start_time)),
            })
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return render_template('pages/shows.html', shows=body)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    body = {}
    try:
        req = request.form
        venue_id = req['venue_id']
        artist_id = req['artist_id']
        start_time = req['start_time']
        show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
        db.session.add(show)
        db.session.commit()
    except:
        db.session.rollback()
        error = False
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
