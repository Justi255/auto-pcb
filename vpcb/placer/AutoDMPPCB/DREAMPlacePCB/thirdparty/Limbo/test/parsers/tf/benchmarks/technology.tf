; Technology File NCSU FreePDK 45nm

;********************************
; LAYER DEFINITION
;********************************
layerDefinitions(

 techLayers(
 ;( LayerName                 Layer#     Abbreviation )
 ;( ---------                 ------     ------------ )
  ( IP                        63         IP )
  ( nwell                     3          nwell )
  ( pwell                     2          pwell )
  ( nimplant                  4          nimplant )
  ( pimplant                  5          pimplant )
  ( active                    1          active )
  ( vtg                       6          vtg )
  ( vth                       7          vth )
  ( thkox                     8          thkox )
  ( poly                      9          poly )
  ( contact                   10         contact )
  ( metal1                    11         metal1 )
  ( via1                      12         via1 )
  ( metal2                    13         metal2 )
  ( via2                      14         via2 )
  ( metal3                    15         metal3 )
  ( via3                      16         via3 )
  ( metal4                    17         metal4 )
  ( via4                      18         via4 )
  ( metal5                    19         metal5 )
  ( via5                      20         via5 )
  ( metal6                    21         metal6 )
  ( via6                      22         via6 )
  ( metal7                    23         metal7 )
  ( via7                      24         via7 )
  ( metal8                    25         metal8 )
  ( via8                      26         via8 )
  ( metal9                    27         metal9 )
  ( via9                      28         via9 )
  ( metal10                   29         metal10 )
  ( DRC                       400        DRC )
 ) ;techLayers

 techLayerPurposePriorities(
 ;layers are ordered from lowest to highest priority
 ;( LayerName                 Purpose    )
 ;( ---------                 -------    )
  ( IP                        drawing )
  ( nwell                     drawing )
  ( pwell                     drawing )
  ( nimplant                  drawing )
  ( pimplant                  drawing )
  ( active                    drawing )
  ( vtg                       drawing )
  ( vth                       drawing )
  ( thkox                     drawing )
  ( poly                      drawing )
  ( contact                   drawing )
  ( metal1                    drawing )
  ( via1                      drawing )
  ( metal2                    drawing )
  ( via2                      drawing )
  ( metal3                    drawing )
  ( via3                      drawing )
  ( metal4                    drawing )
  ( via4                      drawing )
  ( metal5                    drawing )
  ( via5                      drawing )
  ( metal6                    drawing )
  ( via6                      drawing )
  ( metal7                    drawing )
  ( via7                      drawing )
  ( metal8                    drawing )
  ( via8                      drawing )
  ( metal9                    drawing )
  ( via9                      drawing )
  ( metal10                   drawing )
  ( DRC                       drawing )
 ) ;techLayerPurposePriorities

 techDisplays(
 ;( LayerName    Purpose      Packet          Vis Sel Con2ChgLy DrgEnbl Valid )
 ;( ---------    -------      ------          --- --- --------- ------- ----- )
  ( IP           drawing      PacketName_0     t t t t t )
  ( nwell        drawing      PacketName_2     t t t t t )
  ( pwell        drawing      PacketName_3     t t t t t )
  ( nimplant     drawing      PacketName_4     t t t t t )
  ( pimplant     drawing      PacketName_5     t t t t t )
  ( active       drawing      PacketName_6     t t t t t )
  ( vtg          drawing      PacketName_11    t t t t t )
  ( vth          drawing      PacketName_12    t t t t t )
  ( thkox        drawing      PacketName_13    t t t t t )
  ( poly         drawing      PacketName_14    t t t t t )
  ( contact      drawing      PacketName_19    t t t t t )
  ( metal1       drawing      PacketName_26    t t t t t )
  ( via1         drawing      PacketName_30    t t t t t )
  ( metal2       drawing      PacketName_31    t t t t t )
  ( via2         drawing      PacketName_35    t t t t t )
  ( metal3       drawing      PacketName_36    t t t t t )
  ( via3         drawing      PacketName_40    t t t t t )
  ( metal4       drawing      PacketName_41    t t t t t )
  ( via4         drawing      PacketName_45    t t t t t )
  ( metal5       drawing      PacketName_46    t t t t t )
  ( via5         drawing      PacketName_50    t t t t t )
  ( metal6       drawing      PacketName_51    t t t t t )
  ( via6         drawing      PacketName_55    t t t t t )
  ( metal7       drawing      PacketName_56    t t t t t )
  ( via7         drawing      PacketName_60    t t t t t )
  ( metal8       drawing      PacketName_61    t t t t t )
  ( via8         drawing      PacketName_65    t t t t t )
  ( metal9       drawing      PacketName_66    t t t t t )
  ( via9         drawing      PacketName_70    t t t t t )
  ( metal10      drawing      PacketName_71    t t t t t )
  ( DRC          drawing      PacketName_77    t t t t t )
 ) ;techDisplays

) ;layerDefinitions
