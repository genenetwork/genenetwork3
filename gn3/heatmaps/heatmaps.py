import random
import plotly.express as px

#### Remove these ####

heatmap_dir = "heatmap_images"

def generate_random_data(data_stop: float = 2, width: int = 10, height: int = 30):
    """
    This is mostly a utility function to be used to generate random data, useful
    for development of the heatmap generation code, without access to the actual
    database data.
    """
    return [[random.uniform(0,data_stop) for i in range(0, width)]
            for j in range(0, height)]

def heatmap_x_axis_names():
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
#### END: Remove these ####

# Grey + Blue + Red
def generate_heatmap():
    rows = 20
    data = generate_random_data(height=rows)
    y = (["%s"%x for x in range(1, rows+1)][:-1] + ["X"]) #replace last item with x for now
    fig = px.imshow(
        data,
        x=heatmap_x_axis_names(),
        y=y,
        width=500)
    fig.update_traces(xtype="array")
    fig.update_traces(ytype="array")
    # fig.update_traces(xgap=10)
    fig.update_xaxes(
        visible=True,
        title_text="Traits",
        title_font_size=16)
    fig.update_layout(
        coloraxis_colorscale=[
            [0.0, '#3B3B3B'], [0.4999999999999999, '#ABABAB'],
            [0.5, '#F5DE11'], [1.0, '#FF0D00']])

    fig.write_html("%s/%s"%(heatmap_dir, "test_image.html"))
    return fig
