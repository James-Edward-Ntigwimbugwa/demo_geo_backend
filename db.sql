 Schema |            Name             | Type  |  Owner   
--------+-----------------------------+-------+----------
 public | base_floor                  | table | postgres
 public | corridors                   | table | postgres
 public | nav_edges                   | table | postgres
 public | nav_edges_final             | table | postgres
 public | nav_edges_proj              | table | postgres
 public | nav_edges_work              | table | postgres
 public | nav_edges_work_vertices_pgr | table | postgres
 public | nav_nodes                   | table | postgres
 public | nav_nodes_proj              | table | postgres
 public | nav_nodes_snapped           | table | postgres
 public | room_points                 | table | postgres
 public | route_result                | table | postgres
 public | spatial_ref_sys             | table | postgres
(13 rows)

interactive_maps_demo=# \dt base_floor 
           List of relations
 Schema |    Name    | Type  |  Owner   
--------+------------+-------+----------
 public | base_floor | table | postgres
(1 row)

interactive_maps_demo=# \d base_floor
                                         Table "public.base_floor"
    Column    |         Type          | Collation | Nullable |                   Default                   
--------------+-----------------------+-----------+----------+---------------------------------------------
 ogc_fid      | integer               |           | not null | nextval('base_floor_ogc_fid_seq'::regclass)
 wkb_geometry | geometry(LineStringZ) |           |          | 
 layer        | character varying     |           |          | 
 paperspace   | boolean               |           |          | 
 subclasses   | character varying     |           |          | 
 linetype     | character varying     |           |          | 
 entityhandle | character varying     |           |          | 
 text         | character varying     |           |          | 
Indexes:
    "base_floor_pk" PRIMARY KEY, btree (ogc_fid)
    "base_floor_wkb_geometry_geom_idx" gist (wkb_geometry)

interactive_maps_demo=# \d corridors
                                           Table "public.corridors"
    Column    |           Type            | Collation | Nullable |                  Default                   
--------------+---------------------------+-----------+----------+--------------------------------------------
 ogc_fid      | integer                   |           | not null | nextval('corridors_ogc_fid_seq'::regclass)
 wkb_geometry | geometry(LineString,4326) |           |          | 
 fid          | numeric(20,0)             |           |          | 
 label        | character varying         |           |          | 
 type         | character varying         |           |          | 
Indexes:
    "corridors_pk" PRIMARY KEY, btree (ogc_fid)
    "corridors_wkb_geometry_geom_idx" gist (wkb_geometry)

interactive_maps_demo=# \d nav_edges
                                           Table "public.nav_edges"
    Column    |           Type            | Collation | Nullable |                  Default                   
--------------+---------------------------+-----------+----------+--------------------------------------------
 ogc_fid      | integer                   |           | not null | nextval('nav_edges_ogc_fid_seq'::regclass)
 wkb_geometry | geometry(LineString,4326) |           |          | 
 fid          | numeric(20,0)             |           |          | 
 label        | character varying         |           |          | 
 from_id      | numeric(10,0)             |           |          | 
 to_id        | numeric(10,0)             |           |          | 
Indexes:
    "nav_edges_pk" PRIMARY KEY, btree (ogc_fid)
    "nav_edges_wkb_geometry_geom_idx" gist (wkb_geometry)

interactive_maps_demo=# \d nav_edges_final
                   Table "public.nav_edges_final"
 Column |           Type            | Collation | Nullable | Default 
--------+---------------------------+-----------+----------+---------
 id     | integer                   |           | not null | 
 geom   | geometry(LineString,3857) |           |          | 
 label  | text                      |           |          | 
 cost   | double precision          |           |          | 
Indexes:
    "nav_edges_final_pkey" PRIMARY KEY, btree (id)
    "nav_edges_final_geom_idx" gist (geom)

interactive_maps_demo=# \d nav_edges_p
Did not find any relation named "nav_edges_p".
interactive_maps_demo=# \d nav_edges_p
nav_edges_pk             nav_edges_proj           nav_edges_proj_geom_idx  nav_edges_proj_id_seq    nav_edges_proj_pkey      
interactive_maps_demo=# \d nav_edges_proj
                                     Table "public.nav_edges_proj"
 Column |           Type            | Collation | Nullable |                  Default                   
--------+---------------------------+-----------+----------+--------------------------------------------
 id     | integer                   |           | not null | nextval('nav_edges_proj_id_seq'::regclass)
 geom   | geometry(LineString,3857) |           |          | 
 label  | text                      |           |          | 
 cost   | double precision          |           |          | 
Indexes:
    "nav_edges_proj_pkey" PRIMARY KEY, btree (id)
    "nav_edges_proj_geom_idx" gist (geom)

interactive_maps_demo=# \d nav_edges_work
               Table "public.nav_edges_work"
 Column |       Type       | Collation | Nullable | Default 
--------+------------------+-----------+----------+---------
 id     | integer          |           | not null | 
 geom   | geometry         |           |          | 
 cost   | double precision |           |          | 
 source | integer          |           |          | 
 target | integer          |           |          | 
Indexes:
    "nav_edges_work_pkey" PRIMARY KEY, btree (id)
    "nav_edges_work_geom_idx" gist (geom)
    "nav_edges_work_source_idx" btree (source)
    "nav_edges_work_target_idx" btree (target)

interactive_maps_demo=# \d nav_edges_work_vertices_pgr
                                    Table "public.nav_edges_work_vertices_pgr"
  Column  |         Type         | Collation | Nullable |                         Default                         
----------+----------------------+-----------+----------+---------------------------------------------------------
 id       | bigint               |           | not null | nextval('nav_edges_work_vertices_pgr_id_seq'::regclass)
 cnt      | integer              |           |          | 
 chk      | integer              |           |          | 
 ein      | integer              |           |          | 
 eout     | integer              |           |          | 
 the_geom | geometry(Point,3857) |           |          | 
Indexes:
    "nav_edges_work_vertices_pgr_pkey" PRIMARY KEY, btree (id)
    "nav_edges_work_vertices_pgr_the_geom_idx" gist (the_geom)

interactive_maps_demo=# \d nav_nodes
                                        Table "public.nav_nodes"
    Column    |         Type         | Collation | Nullable |                  Default                   
--------------+----------------------+-----------+----------+--------------------------------------------
 ogc_fid      | integer              |           | not null | nextval('nav_nodes_ogc_fid_seq'::regclass)
 wkb_geometry | geometry(Point,4326) |           |          | 
 fid          | numeric(20,0)        |           |          | 
 label        | character varying    |           |          | 
 node_type    | character varying    |           |          | 
Indexes:
    "nav_nodes_pk" PRIMARY KEY, btree (ogc_fid)
    "nav_nodes_wkb_geometry_geom_idx" gist (wkb_geometry)

interactive_maps_demo=# \d nav_nodes_proj
                                    Table "public.nav_nodes_proj"
  Column   |         Type         | Collation | Nullable |                  Default                   
-----------+----------------------+-----------+----------+--------------------------------------------
 id        | integer              |           | not null | nextval('nav_nodes_proj_id_seq'::regclass)
 geom      | geometry(Point,3857) |           |          | 
 label     | text                 |           |          | 
 node_type | text                 |           |          | 
Indexes:
    "nav_nodes_proj_pkey" PRIMARY KEY, btree (id)
    "nav_nodes_proj_geom_idx" gist (geom)

interactive_maps_demo=# \d nav_nodes_snapped
           Table "public.nav_nodes_snapped"
  Column   |   Type   | Collation | Nullable | Default 
-----------+----------+-----------+----------+---------
 id        | integer  |           |          | 
 geom      | geometry |           |          | 
 label     | text     |           |          | 
 node_type | text     |           |          | 
Indexes:
    "nav_nodes_snapped_geom_idx" gist (geom)

interactive_maps_demo=# \d ro
room_points                        room_points_pk                     route_result                       
room_points_ogc_fid_seq            room_points_wkb_geometry_geom_idx  route_result_geom_idx              
interactive_maps_demo=# \d room_points
                                       Table "public.room_points"
    Column    |       Type        | Collation | Nullable |                   Default                    
--------------+-------------------+-----------+----------+----------------------------------------------
 ogc_fid      | integer           |           | not null | nextval('room_points_ogc_fid_seq'::regclass)
 wkb_geometry | geometry(PointZ)  |           |          | 
 layer        | character varying |           |          | 
 paperspace   | boolean           |           |          | 
 subclasses   | character varying |           |          | 
 linetype     | character varying |           |          | 
 entityhandle | character varying |           |          | 
 text         | character varying |           |          | 
Indexes:
    "room_points_pk" PRIMARY KEY, btree (ogc_fid)
    "room_points_wkb_geometry_geom_idx" gist (wkb_geometry)

interactive_maps_demo=# \d route_result
                Table "public.route_result"
 Column |       Type       | Collation | Nullable | Default 
--------+------------------+-----------+----------+---------
 seq    | integer          |           |          | 
 node   | bigint           |           |          | 
 edge   | bigint           |           |          | 
 cost   | double precision |           |          | 
 geom   | geometry         |           |          | 
Indexes:
    "route_result_geom_idx" gist (geom)

