"""
Test the qtlfiles export of traits files

Run with:

    env SQL_URI="mysql://<user>:<password>@<host>:<port>/db_webqtl" python3 qtlfilesexport.py

replacing the variables in the angled brackets with the appropriate values
"""
from gn3.random import random_string
from gn3.computations.slink import slink
from gn3.db_utils import database_connector
from gn3.computations.qtlreaper import run_reaper
from gn3.db.traits import retrieve_trait_data, retrieve_trait_info
from gn3.computations.heatmap import export_trait_data, get_nearest_marker
from gn3.db.genotypes import (
    build_genotype_file,
    parse_genotype_file,
    load_genotype_samples)
from gn3.computations.heatmap import (
    cluster_traits,
    compute_traits_order,
    retrieve_strains_and_values)
from gn3.computations.qtlreaper import (
    generate_traits_file,
    chromosome_sorter_key_fn,
    parse_reaper_main_results,
    organise_reaper_main_results,
    parse_reaper_permutation_results)

import plotly.express as px

## for dendrogram
import numpy as np
import plotly.graph_objects as go
import plotly.figure_factory as ff

# for single heatmap
from plotly.subplots import make_subplots

TMPDIR = "tmp/"

def trait_fullnames():
    """Return sample names for traits"""
    return [
        "UCLA_BXDBXH_CARTILAGE_V2::ILM103710672",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM2260338",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM3140576",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM5670577",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM2070121",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM103990541",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM1190722",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM6590722",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM4200064",
        "UCLA_BXDBXH_CARTILAGE_V2::ILM3140463"]

def get_lrs_from_chr(trait, chr_name):
    chromosome = trait["chromosomes"].get(chr_name)
    if chromosome:
        return [
            locus["LRS"] for locus in
            sorted(chromosome["loci"], key=lambda loc: loc["Locus"])]
    return [None]

def process_traits_data_for_heatmap(data, trait_names, chromosome_names):
    print("TRAIT_NAMES: {}".format(trait_names))
    print("chromosome names: {}".format(chromosome_names))
    print("data keys: {}".format(data.keys()))
    hdata = [
        [get_lrs_from_chr(data[trait], chr_name) for trait in trait_names]
        for chr_name in chromosome_names]
    # print("hdata: {}".format(hdata))
    return hdata

def generate_heatmap(
        data, image_filename_prefix, x_axis = None, x_label: str = "",
        y_axis = None, y_label: str = "", output_dir: str = TMPDIR):
    """Generate single heatmap section."""
    print("X-AXIS:({}, {}), Y-AXIS: ({}, {}), ROWS:{}, COLS:{}".format(
        x_axis, (len(x_axis) if x_axis else 0),
        y_axis, (len(y_axis) if y_axis else 0),
        len(data), len(data[0])))
    fig = px.imshow(
        data,
        x = x_axis,
        y = y_axis,
        width=1000
    )
    fig.update_yaxes(title=y_label)
    fig.update_xaxes(title=x_label)
    image_filename = "{}/{}.html".format(output_dir, image_filename_prefix)
    fig.write_html(image_filename)
    return image_filename, fig

def generate_dendrogram(
        data, image_filename_prefix, x_axis = None, x_label: str = "",
        y_axis = None, y_label: str = "", output_dir: str = TMPDIR):
    fig = ff.create_dendrogram(
        np.array(data), orientation="right", labels=y_axis)

    heatmap = go.Heatmap(
        x=fig['layout']['xaxis']['ticktext'],
        y=fig['layout']['yaxis']['ticktext'],
        z=data)
    
    # print("HEAMAP:{}".format(heatmap))
    fig.add_trace(heatmap)

    fig.update_layout({"width": 1000, "height": 500})
    image_filename = "{}/{}.html".format(output_dir, image_filename_prefix)
    fig.write_html(image_filename)
    return image_filename, fig

def generate_single_heatmap(
        data, image_filename_prefix, x_axis = None, x_label: str = "",
        y_axis = None, y_label: str = "", output_dir: str = TMPDIR):
    """Generate single heatmap section."""
    # fig = go.Figure({"type": "heatmap"})
    num_cols = len(x_axis)
    fig = make_subplots(
        rows=1,
        cols=num_cols,
        shared_yaxes="rows",
        # horizontal_spacing=(1 / (num_cols - 1)),
        subplot_titles=x_axis
    )
    hms = [go.Heatmap(
        name=chromo,
        y = y_axis,
        z = data_array,
        showscale=False) for chromo, data_array in zip(x_axis, data)]
    for col, hm in enumerate(hms):
        fig.add_trace(hm, row=1, col=(col + 1))

    fig.update_traces(
        showlegend=False,
        colorscale=[
            [0.0, '#3B3B3B'], [0.4999999999999999, '#ABABAB'],
            [0.5, '#F5DE11'], [1.0, '#FF0D00']],
        selector={"type": "heatmap"})
    fig.update_traces(
        showlegend=True,
        showscale=True,
        selector={"name": x_axis[-1]})
    fig.update_layout(
        coloraxis_colorscale=[
            [0.0, '#3B3B3B'], [0.4999999999999999, '#ABABAB'],
            [0.5, '#F5DE11'], [1.0, '#FF0D00']]
    )
    print(fig)
    image_filename = "{}/{}.html".format(output_dir, image_filename_prefix)
    fig.write_html(image_filename)
    return image_filename, fig

def main():
    """entrypoint function"""
    conn = database_connector()[0]
    threshold = 0
    traits = [
        retrieve_trait_info(threshold, fullname, conn)
        for fullname in trait_fullnames()]
    traits_data_list = [retrieve_trait_data(t, conn) for t in traits]
    genotype_filename = build_genotype_file(traits[0]["riset"])
    genotype = parse_genotype_file(genotype_filename)
    strains = load_genotype_samples(genotype_filename)
    exported_traits_data_list = [
        export_trait_data(td, strains) for td in traits_data_list]
    slinked = slink(cluster_traits(exported_traits_data_list))
    print("SLINKED: {}".format(slinked))
    traits_order = compute_traits_order(slinked)
    print("KEYS: {}".format(traits[0].keys()))
    ordered_traits_names = [
        traits[idx]["trait_fullname"] for idx in traits_order]
    print("ORDERS: {}".format(traits_order))
    strains_and_values = retrieve_strains_and_values(
        traits_order, strains, exported_traits_data_list)
    strains_values = strains_and_values[0][1]
    trait_values = [t[2] for t in strains_and_values]
    traits_filename = "{}/traits_test_file_{}.txt".format(
        TMPDIR, random_string(10))
    generate_traits_file(strains_values, trait_values, traits_filename)
    print("Generated file: {}".format(traits_filename))

    main_output, permutations_output = run_reaper(
        genotype_filename, traits_filename, separate_nperm_output=True)

    print("Main output: {}, Permutation output: {}".format(
        main_output, permutations_output))

    qtlresults = parse_reaper_main_results(main_output)
    permudata = parse_reaper_permutation_results(permutations_output)
    # print("QTLRESULTS: {}".format(qtlresults))
    # print("PERMUDATA: {}".format(permudata))

    nearest = get_nearest_marker(traits, genotype)
    print("NEAREST: {}".format(nearest))

    organised = organise_reaper_main_results(qtlresults)

    traits_ids = [# sort numerically, but retain the ids as strings
        str(i) for i in sorted({int(row["ID"]) for row in qtlresults})]
    chromosome_names = sorted(
        {row["Chr"] for row in qtlresults}, key = chromosome_sorter_key_fn)
    loci_names = sorted({row["Locus"] for row in qtlresults})
    ordered_traits_names = {
        res_id: trait for res_id, trait in
        zip(traits_ids,
            [traits[idx]["trait_fullname"] for idx in traits_order])}
    # print("ordered:{}, original: {}".format(
    #     ordered_traits_names, [t["trait_fullname"] for t in traits]))
    # print("chromosome_names:{}".format(chromosome_names))
    # print("trait_ids:{}".format(traits_ids))
    # print("loci names:{}".format(loci_names))
    hdata = process_traits_data_for_heatmap(organised, traits_ids, chromosome_names)

    # print("ZIPPED: {}".format(zip(tuple(ordered_traits_names.keys()), hdata)))
    # print("HDATA LENGTH:{}, ORDERED TRAITS LENGTH:{}".format(len(hdata), len(ordered_traits_names.keys())))
    heatmaps_data = [
        generate_heatmap(
            data,
            "heatmap_chr{}_{}".format(chromo, random_string(10)),
            y_axis=tuple(
                ordered_traits_names[traits_ids[order]]
                for order in traits_order),
            x_label=chromo,
            output_dir=TMPDIR)
        for chromo, data in zip(chromosome_names, hdata)]
    print("IMAGES FILENAMES: {}".format([img[0] for img in heatmaps_data]))

    dendograms_data = [
        generate_dendrogram(
            data,
            "dendo_chr{}_{}".format(chromo, random_string(10)),
            y_axis=tuple(
                ordered_traits_names[traits_ids[order]]
                for order in traits_order),
            x_label=chromo,
            output_dir=TMPDIR)
        for chromo, data in zip(chromosome_names, hdata)]

    res = generate_single_heatmap(
        hdata,
        "single_heatmap_{}".format(random_string(10)),
        y_axis=tuple(
            ordered_traits_names[traits_ids[order]]
                for order in traits_order),
        y_label="Traits",
        x_axis=[chromo for chromo in chromosome_names],
        x_label="Chromosomes",
        output_dir=TMPDIR)

if __name__ == "__main__":
    main()
