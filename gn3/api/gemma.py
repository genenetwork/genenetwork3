"""Endpoints for running the gemma cmd"""
import os
import redis

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.commands import queue_cmd
from gn3.commands import run_cmd
from gn3.file_utils import jsonfile_to_dict
from gn3.computations.gemma import generate_gemma_cmd
from gn3.computations.gemma import do_paths_exist
from gn3.computations.gemma import generate_hash_of_string
from gn3.computations.gemma import generate_pheno_txt_file
from gn3.computations.gemma import generate_gemma_computation_cmd

gemma = Blueprint("gemma", __name__)


@gemma.route("/version")
def get_version():
    """Display the installed version of gemma-wrapper"""
    gemma_cmd = current_app.config["GEMMA_WRAPPER_CMD"]
    return jsonify(run_cmd(f"{gemma_cmd} -v | head -n 1"))


# This is basically extracted from genenetwork2
# wqflask/wqflask/marker_regression/gemma_ampping.py
@gemma.route("/k-gwa-computation", methods=["POST"])
def run_gemma():
    """Generates a command for generating K-Values and then later, generate a GWA
command that contains markers. These commands are queued; and the expected
file output is returned.

    """
    data = request.get_json()
    app_defaults = current_app.config
    __hash = generate_hash_of_string(f"{data.get('genofile_name')}_"
                                     ''.join(data.get("values", "")))
    gemma_kwargs = {
        "geno_filename":
        os.path.join(app_defaults.get("GENODIR"), "bimbam",
                     f"{data.get('geno_filename')}"),
        "trait_filename":
        generate_pheno_txt_file(
            tmpdir=app_defaults.get("TMPDIR"),
            values=data.get("values"),
            # Generate this file on the fly!
            trait_filename=(f"{data.get('dataset_groupname')}_"
                            f"{data.get('trait_name')}_"
                            f"{__hash}.txt"))
    }
    gemma_wrapper_kwargs = {}
    if data.get("loco"):
        gemma_wrapper_kwargs["loco"] = f"--input {data.get('loco')}"
    k_computation_cmd = generate_gemma_computation_cmd(
        gemma_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_wrapper_kwargs={"loco": f"--input {data.get('loco')}"},
        gemma_kwargs=gemma_kwargs,
        output_file=(f"{app_defaults.get('TMPDIR')}/gn2/"
                     f"{data.get('dataset_name')}_K_"
                     f"{__hash}.json"))
    gemma_kwargs["lmm"] = data.get("lmm", 9)
    gemma_wrapper_kwargs["input"] = (f"{data.get('dataset_name')}_K_"
                                     f"{__hash}.json")
    gwa_cmd = generate_gemma_computation_cmd(
        gemma_wrapper_kwargs=gemma_wrapper_kwargs,
        gemma_cmd=app_defaults.get("GEMMA_WRAPPER_CMD"),
        gemma_kwargs=gemma_kwargs,
        output_file=(f"{data.get('dataset_name')}_GWA_"
                     f"{__hash}.txt"))
    if not all([k_computation_cmd, gwa_cmd]):
        return jsonify(status=128,
                       error="Unable to generate cmds for computation!"), 500
    return jsonify(unique_id=queue_cmd(
        conn=redis.Redis(),
        email=data.get("email"),
        job_queue=app_defaults.get("REDIS_JOB_QUEUE"),
        cmd=f"{k_computation_cmd} && {gwa_cmd}"),
                   status="queued",
                   output_file=(f"{data.get('dataset_name')}_GWA_"
                                f"{__hash}.txt"))


@gemma.route("/status/<unique_id>", methods=["GET"])
def check_cmd_status(unique_id):
    """Given a (url-encoded) UNIQUE-ID which is returned when hitting any of the
gemma endpoints, return the status of the command

    """
    status = redis.Redis().hget(name=unique_id, key="status")
    if not status:
        return jsonify(status=128,
                       error="The unique id you used does not exist!"), 500
    return jsonify(status=status.decode("utf-8"))


@gemma.route("/k-compute/<token>", methods=["POST"])
def compute_k(token):
    """Given a genofile, traitfile, snpsfile, and the token, compute the k-valuen
and return <hash-of-inputs>.json with a UNIQUE-ID of the job. The genofile,
traitfile, and snpsfile are extracted from a metadata.json file.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs)
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/k-compute/loco/<chromosomes>/<token>", methods=["POST"])
def compute_k_loco(chromosomes, token):
    """Similar to 'compute_k' with the extra option of using loco given chromosome
values.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            chromosomes=chromosomes)
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/gwa-compute/<k_filename>/<token>", methods=["POST"])
def compute_gwa(k_filename, token):
    """Compute GWA values. No loco no covariates provided.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        gemma_kwargs = {
            "g": genofile,
            "p": phenofile,
            "a": snpsfile,
            "lmm": _dict.get("lmm", 9)
        }
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "input": os.path.join(working_dir, k_filename)
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/gwa-compute/covars/<k_filename>/<token>", methods=["POST"])
def compute_gwa_with_covar(k_filename, token):
    """Compute GWA values. No Loco; Covariates provided.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile, covarfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps", "covar"]
        ]
        gemma_kwargs = {
            "g": genofile,
            "p": phenofile,
            "a": snpsfile,
            "c": covarfile,
            "lmm": _dict.get("lmm", 9)
        }
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "input": os.path.join(working_dir, k_filename)
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/gwa-compute/<k_filename>/loco/maf/<maf>/<token>",
             methods=["POST"])
def compute_gwa_with_loco_maf(k_filename, maf, token):
    """Compute GWA values. No Covariates provided. Only loco and maf vals given.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {
            "g": genofile,
            "p": phenofile,
            "a": snpsfile,
            "lmm": _dict.get("lmm", 9),
            'maf': float(maf)
        }
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "loco": f"--input {os.path.join(working_dir, k_filename)}"
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/gwa-compute/<k_filename>/loco/covariates/maf/<maf>/<token>",
             methods=["POST"])
def compute_gwa_with_loco_covar(k_filename, maf, token):
    """Compute GWA values. No Covariates provided. Only loco and maf vals given.

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile, covarfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps", "covar"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile, covarfile]):
            raise FileNotFoundError
        gemma_kwargs = {
            "g": genofile,
            "p": phenofile,
            "a": snpsfile,
            "c": covarfile,
            "lmm": _dict.get("lmm", 9),
            "maf": float(maf)
        }
        results = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "loco": f"--input {os.path.join(working_dir, k_filename)}"
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=results.get("gemma_cmd")),
                       status="queued",
                       output_file=results.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/k-gwa-compute/<token>", methods=["POST"])
def compute_k_gwa(token):
    """Given a genofile, traitfile, snpsfile, and the token, compute the k-values
and return <hash-of-inputs>.json with a UNIQUE-ID of the job. The genofile,
traitfile, and snpsfile are extracted from a metadata.json file. No Loco no
covars; lmm defaults to 9!

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        gemma_k_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs)
        gemma_kwargs["lmm"] = _dict.get("lmm", 9)
        gemma_gwa_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "input": os.path.join(working_dir,
                                      gemma_k_cmd.get("output_file"))
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=(f"{gemma_k_cmd.get('gemma_cmd')} && "
                 f"{gemma_gwa_cmd.get('gemma_cmd')}")),
                       status="queued",
                       output_file=gemma_gwa_cmd.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/k-gwa-compute/covars/<token>", methods=["POST"])
def compute_k_gwa_with_covars_only(token):
    """Given a genofile, traitfile, snpsfile, and the token, compute the k-values
and return <hash-of-inputs>.json with a UNIQUE-ID of the job. The genofile,
traitfile, and snpsfile are extracted from a metadata.json file. No Loco no
covars; lmm defaults to 9!

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile, covarfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps", "covar"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        gemma_k_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs)
        gemma_kwargs["c"] = covarfile
        gemma_kwargs["lmm"] = _dict.get("lmm", 9)
        gemma_gwa_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "input": os.path.join(working_dir,
                                      gemma_k_cmd.get("output_file"))
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=(f"{gemma_k_cmd.get('gemma_cmd')} && "
                 f"{gemma_gwa_cmd.get('gemma_cmd')}")),
                       status="queued",
                       output_file=gemma_gwa_cmd.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/k-gwa-compute/loco/<chromosomes>/maf/<maf>/<token>",
             methods=["POST"])
def compute_k_gwa_with_loco_only(chromosomes, maf, token):
    """k-gwa-compute; Loco no covars; lmm defaults to 9!

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        gemma_k_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            chromosomes=chromosomes)
        gemma_kwargs["maf"] = float(maf)
        gemma_kwargs["lmm"] = _dict.get("lmm", 9)
        gemma_gwa_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "loco":
                ("--input "
                 f"{os.path.join(working_dir, gemma_k_cmd.get('output_file'))}"
                 )
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=(f"{gemma_k_cmd.get('gemma_cmd')} && "
                 f"{gemma_gwa_cmd.get('gemma_cmd')}")),
                       status="queued",
                       output_file=gemma_gwa_cmd.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")


@gemma.route("/k-gwa-compute/covars/loco/<chromosomes>/maf/<maf>/<token>",
             methods=["POST"])
def compute_k_gwa_with_loco_and_cavar(chromosomes, maf, token):
    """k-gwa-compute; Loco with covars; lmm defaults to 9!

    """
    working_dir = os.path.join(current_app.config.get("TMPDIR"), token)
    _dict = jsonfile_to_dict(os.path.join(working_dir, "metadata.json"))
    try:
        genofile, phenofile, snpsfile, covarfile = [
            os.path.join(working_dir, _dict.get(x))
            for x in ["geno", "pheno", "snps", "covar"]
        ]
        if not do_paths_exist([genofile, phenofile, snpsfile]):
            raise FileNotFoundError
        gemma_kwargs = {"g": genofile, "p": phenofile, "a": snpsfile}
        gemma_k_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            chromosomes=chromosomes)
        gemma_kwargs["c"] = covarfile
        gemma_kwargs["maf"] = float(maf)
        gemma_kwargs["lmm"] = _dict.get("lmm", 9)
        gemma_gwa_cmd = generate_gemma_cmd(
            gemma_cmd=current_app.config.get("GEMMA_"
                                             "WRAPPER_CMD"),
            output_dir=current_app.config.get('TMPDIR'),
            token=token,
            gemma_kwargs=gemma_kwargs,
            gemma_wrapper_kwargs={
                "loco":
                ("--input "
                 f"{os.path.join(working_dir, gemma_k_cmd.get('output_file'))}"
                 )
            })
        return jsonify(unique_id=queue_cmd(
            conn=redis.Redis(),
            email=(request.get_json() or {}).get('email'),
            job_queue=current_app.config.get("REDIS_JOB_QUEUE"),
            cmd=(f"{gemma_k_cmd.get('gemma_cmd')} && "
                 f"{gemma_gwa_cmd.get('gemma_cmd')}")),
                       status="queued",
                       output_file=gemma_gwa_cmd.get("output_file"))
    # pylint: disable=W0703
    except Exception:
        return jsonify(
            status=128,
            # use better message
            message="Metadata file non-existent!")
