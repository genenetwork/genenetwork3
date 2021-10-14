"""module contains endpoints for ctl"""

# so small 

from flask import Blueprint
from flask import request
from flask import jsonify


ctl = Blueprint("ctl",__name__)

@ctl.route("/run_ctl",methods=["POST"])
def run_ctl():
	"""endpoint to run ctl"""
	ctl_data = request.json

	return "hello"