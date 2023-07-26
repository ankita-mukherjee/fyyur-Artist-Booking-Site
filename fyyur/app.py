# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from typing import Callable
from flask import abort


import sys

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
app.app_context().push()
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)
db.create_all()
# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = "Venue"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    shows = db.relationship("Shows", backref="venue", lazy=True)

    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = "Artist"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))

    shows = db.relationship("Shows", backref="artist", lazy=True)
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Shows(db.Model):
    __tablename__ = "Shows"
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey("Artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("Venue.id"), nullable=False)
    start_time = db.Column(db.String())


db.create_all()
# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data.
    # num_shows should be aggregated based on the number of upcoming shows per venue.
    cities = db.session.query(Venue.city, Venue.state).distinct()
    data = []
    for city, state in cities:
        venues = Venue.query.filter_by(city=city, state=state).all()
        venues_data = []
        for venue in venues:
            venues_data.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": 0,
                }
            )
        data.append(
            {
                "city": city,
                "state": state,
                "venues": venues_data,
            }
        )
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get("search_term")
    search_results = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    response = {
        "count": len(search_results),
        "data": [
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": 0,
            }
            for venue in search_results
        ],
    }
    return render_template(
        "pages/search_venues.html", results=response, search_term=search_term
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    shows = (
        db.session.query(Shows, Artist)
        .join(Artist)
        .filter(Shows.venue_id == venue_id)
        .all()
    )
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()

    if shows is not None:
        for show, artist in shows:
            show_start_time = datetime.strptime(show.start_time, "%Y-%m-%d %H:%M:%S")
            show_data = {
                "artist_id": artist.id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": show.start_time,
            }
            if show_start_time > current_time:
                upcoming_shows.append(show_data)
            else:
                past_shows.append(show_data)

    data = {
        "id": venue_id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website_link": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": False,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    form = VenueForm(request.form)
    if form.validate():
        venue = Venue()
        form.populate_obj(venue)
        try:
            db.session.add(venue)
            db.session.commit()
            flash("Venue " + venue.name + " was successfully listed!")
        except Exception as e:
            print(str(e))
            db.session.rollback()
            flash("An error occurred. Venue " + venue.name + " could not be listed.")
        finally:
            db.session.close()
    else:
        flash("An error occurred. Venue could not be listed. Please check your inputs.")
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    try:
        db.session.delete(venue)
        db.session.commit()
        flash("Venue was successfully deleted!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        flash("An error occurred. Venue could not be deleted.")
    finally:
        db.session.close()
    return redirect(url_for("venues"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO: replace with real data returned from querying the database
    data = Artist.query.order_by("id").all()
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get("search_term")
    result = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
    data = []
    for artist in result:
        data.append({"id": artist.id, "name": artist.name, "num_upcoming_shows": 0})
    response = {"count": len(result), "data": data}
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    artist = Artist.query.get(artist_id)
    shows = (
        db.session.query(Shows, Artist, Venue)
        .join(Artist)
        .join(Venue)
        .filter(Shows.show_id == Artist.id)
        .filter(Shows.venue_id == Venue.id)
        .filter(Artist.id == artist_id)
        .all()
    )
    past_shows = []
    upcoming_shows = []
    for s in shows:
        past_shows.append(
            {
                "venue_id": s.Venue.id,
                "venue_name": s.Venue.name,
                "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
                "start_time": s.Shows.start_time,
            }
        )
    data = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website_link": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_talent": False,
        "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
        "seeking_description": artist.seeking_description,
    }
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    if artist is None:
        abort(404)  # Return a 404 error if the artist doesn't exist

    # Populate the form fields with the artist data
    form.name.data = artist.name
    form.genres.data = artist.genres
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.facebook_link.data = artist.facebook_link
    form.seeking_description.data = artist.seeking_description
    form.image_link.data = artist.image_link
    form.website_link.data = artist.website_link

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # Retrieve the submitted form data
    form = ArtistForm(request.form)

    # Get the existing artist record from the database
    artist = Artist.query.get(artist_id)

    if artist is None:
        abort(404)  # Return a 404 error if the artist doesn't exist

    # Update the artist record with the new attributes from the form
    artist.name = form.name.data
    artist.genres = form.genres.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.seeking_description = form.seeking_description.data
    artist.website_link = form.website_link.data

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    if venue is None:
        abort(404)  # Return a 404 error if the venue doesn't exist

    # Populate the form fields with the venue data
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.address.data = venue.address
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website_link
    form.facebook_link.data = venue.facebook_link
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # Retrieve the submitted form data
    form = VenueForm(request.form)

    # Get the existing venue record from the database
    venue = Venue.query.get(venue_id)

    if venue is None:
        abort(404)  # Return a 404 error if the venue doesn't exist

    # Update the venue record with the new attributes from the form
    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.address = form.address.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.phone = form.phone.data
    venue.website_link = form.website_link.data
    venue.facebook_link = form.facebook_link.data
    venue.seeking_talent = form.seeking_talent.data
    venue.seeking_description = form.seeking_description.data
    venue.image_link = form.image_link.data

    # Commit the changes to the database
    db.session.commit()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # Retrieve the form data
    form = ArtistForm(request.form)

    # Create a new Artist object with the form data
    artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        website_link=form.website_link.data,
    )

    try:
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash("Artist " + request.form["name"] + " was successfully listed!")
    except:
        db.session.rollback()
        # TODO: on unsuccessful db insert, flash an error instead.
        flash(
            "An error occurred. Artist "
            + request.form["name"]
            + " could not be listed."
        )
    finally:
        db.session.close()
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------
@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    #       num_shows should be aggregated based on number of upcoming shows per venue.

    data = []
    shows = Shows.query.all()

    for show in shows:
        # Can reference show.artist, show.venue
        data.append(
            {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time)),
            }
        )
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create", methods=["GET"])
def create_show_form():
    # renders form. do not touch.
    form = ShowForm()
    if form.validate_on_submit():
        # TODO: Process the form data and save it to the database
        flash("Show successfully created!")
        return redirect(url_for("home"))
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm(request.form)
    # called to create new shows in the db, upon submitting the new show listing form
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data
    # TODO: insert form data as a new Show record in the db, instead
    show = Shows(show_id=artist_id, venue_id=venue_id, start_time=start_time)
    # on successful db insert, flash success
    try:
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except Exception as e:
        print(str(e))
        db.session.rollback()
        flash("An error occurred. Show could not be listed.")
    finally:
        db.session.close()
    # TODO: on unsuccessful db insert, flash an error instead.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error: Exception) -> Callable:
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error: Exception) -> Callable:
    return render_template("errors/500.html"), 500


if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
