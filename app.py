import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import database

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    """
    Renders the main dashboard page.
    """
    return render_template("index.html")

@app.route("/api/filters", methods=["GET"])
def get_filters():
    """
    Returns lists of active release years and levels for filter dropdowns.
    """
    try:
        filters = database.get_filter_options()
        return jsonify(filters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/records", methods=["GET"])
def get_records():
    """
    Returns filtered and searched records for all three categories.
    """
    try:
        # Get query parameters for Topography
        topo_search = request.args.get("topo_search", None)
        topo_year = request.args.get("topo_year", None)
        if topo_year is None or topo_year == "":
            topo_year = None
            
        # Get query parameters for DTED
        dted_search = request.args.get("dted_search", None)
        dted_level = request.args.get("dted_level", None)
        if dted_level is None or dted_level == "":
            dted_level = None
        else:
            try:
                dted_level = int(dted_level)
            except ValueError:
                dted_level = None
                
        # Get query parameters for Land Use
        land_search = request.args.get("land_search", None)
        
        # Get query parameters for Sjungu
        sjungu_search = request.args.get("sjungu_search", None)
        
        # Query data from database helper
        topography_list = database.get_topography_data(topo_search, topo_year)
        dted_list = database.get_dted_data(dted_search, dted_level)
        landused_list = database.get_landused_data(land_search)
        sjungu_list = database.get_sjungu_data(sjungu_search)
        
        return jsonify({
            "topography": topography_list,
            "dted": dted_list,
            "landused": landused_list,
            "sjungu": sjungu_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run the application on host and port specified in environment variables
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t", "y", "yes")
    app.run(host=host, port=port, debug=debug)
