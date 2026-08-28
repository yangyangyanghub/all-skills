<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" version="3.34.1-Prizren" styleCategories="AllStyleCategories" simplifyDrawingTol="1" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" maxScale="0" simplifyAlgorithm="0" minScale="100000000" simplifyDrawingHints="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option type="QString" value="" name="name"/>
      <Option name="properties"/>
      <Option type="QString" value="collection" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" type="singlebandpseudocolor" band="1" classifiedMin="0" classifiedMax="5000">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="3" minimumValue="0" maximumValue="5000" clip="0" colorRampType="INTERPOLATED" labelPrecision="4" colorMapInterpolation="Linear">
          <colorPalette>
            <colorPaletteEntry alpha="255" label="低地 (0m)" color="#56A237" value="0"/>
            <colorPaletteEntry alpha="255" label="丘陵 (500m)" color="#BA8E46" value="500"/>
            <colorPaletteEntry alpha="255" label="山地 (1000m)" color="#D4AA6A" value="1000"/>
            <colorPaletteEntry alpha="255" label="高地 (1500m)" color="#C2905A" value="1500"/>
            <colorPaletteEntry alpha="255" label="高原 (2000m)" color="#B08050" value="2000"/>
            <colorPaletteEntry alpha="255" label="高山 (3000m)" color="#8B6914" value="3000"/>
            <colorPaletteEntry alpha="255" label="雪峰 (5000m)" color="#FFFFFF" value="5000"/>
          </colorPalette>
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" value="255,255,255,255" name="color1"/>
              <Option type="QString" value="86,162,21,255" name="color2"/>
              <Option type="QString" value="0" name="direction"/>
              <Option type="QString" value="0" name="discrete"/>
              <Option type="QString" value="gradient" name="rampType"/>
              <Option type="QString" value="rgb" name="spec"/>
            </Option>
          </colorramp>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" gamma="1" contrast="0"/>
    <huesaturation grayscaleMode="0" saturation="0" colorizeOn="0" colorizeStrength="0" colorizeBlue="128" colorizeGreen="128" colorizeRed="255"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
  <layerOpacity>1</layerOpacity>
</qgis>
