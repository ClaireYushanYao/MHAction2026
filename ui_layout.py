from shiny import ui
import ipyleaflet as L
from shinywidgets import output_widget 

geographic_regions = ["County", "House district", "Senate district"]

basemaps = {
    "OpenStreetMap": L.basemaps.OpenStreetMap.Mapnik,
    "Satellite": L.basemaps.Gaode.Satellite,
}

layernames = [
    "Marker MHVillage",
    "Marker LARA",
    "Circle MHVillage (location only)",
    "Circle LARA (location only)",
    "Legislative districts (Michigan State Senate)",
    "Legislative districts (Michigan State House of Representatives)",
]

app_ui = ui.page_fluid(
    ui.HTML("""
        <hr>
        <h1 style="text-align: center; margin-bottom: 10px;"><b>Manufactured Housing Communities in Michigan</b></h1>
        <h2 style="text-align: center; margin-bottom: 40px;
        font-size: 18px; ">Project by <a href="https://www.mhaction.org"
        target="_blank"><i>MH Action</i></a> and
        the <a href="https://ginsberg.umich.edu/ctac" target="_blank"><i>Community Technical Assistance Collaborative</i></a> at the University of Michigan</h2>
    """),
    ui.row(
        ui.column(5,
                  ui.HTML("""
                    <h2 style="text-align: left; font-size: 20px;"><b>About</b></h2>
                    <h3 style="font-size: 16px;">
                    This app is a visualization tool designed to highlight the distribution of manufactured housing communities across Michigan. LARA data was obtained in January 2024 from the Michigan <a href="https://www.michigan.gov/lara" target="_blank">Department of Licensing and Regulatory Affairs</a> via a Freedom of Information Act (<a href="https://michiganlara.govqa.us/WEBAPP/_rs/(S(yu3ftx4zmh34spiozdwicnsn))/supporthome.aspx" target="_blank">FOIA</a>) Request. <a href="https://www.mhvillage.com/Communities/CommunityReport.php" target="_blank">MHVillage</a> data was scraped in December 2023. For more information, visit <a href="https://www.mhaction.org" target="_blank">MHAction.org</a>.

                    <br><br>
                    <h2 style="text-align: left; font-size: 18px;">Definitions</h2>
                    <h3 style="font-size: 16px;">
                    <ul>
                    <li><b>MHC:</b> Manufactured Housing Community</li>
                    <li><b>LARA:</b> Michigan Department of Licensing and Regulatory Affairs. Michigan MHC's are required to register with LARA.</li>
                    <li><b>MHVillage:</b> Online marketplace for buying and selling manufactured homes.</li>
                    </ul>
                    <h2 style="font-size: 18px;"><br>Add Map Layers</h2>
                """),
                  ui.input_select("basemap", "Choose a basemap:", choices=list(basemaps.keys())),
                  ui.input_selectize("layers", "Layers to visualize:", layernames, multiple=True, selected=None),
                  ),
        ui.column(7, output_widget("map", width="auto", height="600px",),
            ui.HTML("</h3> <p style='text-align: center; font-size: 16px;'><i> NOTE: Blue circles are MHC's reported by LARA, orange circles are reported by MHVillage.</i></p>"),),
    ),
    ui.HTML("<hr> <h1><b>Infographics</b></h1>"),
    ui.row(
        ui.HTML("""<hr>"""),
        ui.column(10, ui.output_plot("infographics1")),
        ui.column(2, ui.HTML("<br><br>Need other county data? Download the full table "), ui.download_link("download_info1", "here."))
    ),

    ui.row(
        ui.HTML("""<hr>"""),
        ui.column(10, ui.output_plot("infographics2")),
        ui.column(2, ui.HTML("<br><br>More rent values "), ui.download_link("download_info2", "here.")
        )),

    ui.HTML("""
        <h2 style="text-align: left; margin-bottom: 10px;
        font-size: 16px; "><i>NOTE: Black numbers in the bars represent the number of MHC's included in the calculated average, based on availability of data on MHVillage. For example, the average rent across the 14 reported MHC's in Oakland County is approximately $575.</i></h2>
    """),

    ui.HTML("<hr> <h1><b>Tables</b></h1>"),
    ui.row(
        ui.column(3,
            ui.input_selectize("main_category", "Select a geographic boundary:", choices=geographic_regions),
            ui.output_ui("sub_category_ui"),
            ui.input_selectize("datasource", "Select a source:", choices=[ 'LARA', 'MHVillage'], ),
        ),

    ),
    ui.row(
        ui.column(6,ui.output_table("site_list")),
        ui.column(3, ui.HTML("""
                <h1 style="text-align: left; margin-bottom: 1px;
                font-size: 18px; "<br><br><b>Summary of Location Totals</b></h2>
            """),
            ui.output_table("site_list_summary"),
            ui.download_button("download_data", "Download Table")
        )
    ),
    #ui.tags.div(ui.output_html("district_map"))
    ui.row(
        ui.column(6,ui.HTML("""
        <hr>
        <h1 style="text-align: left; margin-bottom: 10px;"><b>Credits</b></h1>
        <h2 style="text-align: left; margin-bottom: 10px;
        font-size: 16px; ">Project lead: <a href="mailto:hessakh@umich.edu" target="_blank">Hessa Al-Thani</a><br>
        MHAction contact: <a href="mailto:pterranova@mhaction.org" target="_blank">Paul Terranova</a> with support from <a href="mailto:dcampbell@ionia-mi.net" target="_blank">Deb Campbell</a> <br>
        Website development: Naichen Shi <br>
        Web design: Vicky Wang <br>
        Data scraping and collection: Bingqing Xiang<br>
        In partnership with <a href="https://informs.engin.umich.edu/"
        target="_blank">INFORMS</a> at the University of Michigan.</h2><hr>
        """)),
        ui.column(6,ui.HTML("""
        <hr>
        <h1 style="text-align: left; margin-bottom: 10px;"><b>Reference Files</b></h1>
        """),
        ui.download_link("download_mhvillage", "Raw data: MHVillage with coordinates and legislative district .csv"),
        ui.HTML("""
            <br>
        """),
        ui.download_link("download_lara", "Raw data: LARA with coordinates and legislative distric .csv"),
        ui.HTML("""
            <br>
        """),
        ui.download_link("download_house_districts", "Michigan State House Districts 2021 .GeoJSON"),
        ui.HTML("""
            <br>
        """),
        ui.download_link("download_senate_districts", "Michigan State Senate Districts 2021 .GeoJSON"),

        ui.HTML("""
            <hr>
        """)
        )
    ),

    #ui.row(
    #    ui.column(4, ui.output_image("mhaction_logo"), align="center"), 
    #    ui.column(4, ui.output_image("ctac_logo"), align="center"),
    #),
    ui.HTML("""
        <h2 style="text-align: left; margin-bottom: 10px; font-size: 14px;">This is an updated version from June 2024. The original app can be found <a href="https://hessakh.shinyapps.io/michigan_housing1/" target="_blank">here.</a> Updated source code can be found on <a href="https://github.com/viwaumich/mhc" target="_blank">Git.</a> Please reach out to Vicky Wang (<a href="mailto:viwa@umich.edu" target="_blank">viwa@umich.edu</a>) with questions.</h2>
        """),
     #       <h2 style="text-align: left; margin-bottom: 10px;font-size: 18px;
      #  Source code can be found on
       # <a href="https://github.com/soundsinteresting/Michigan_housing/" target="_blank">Git</a> </h2>
)