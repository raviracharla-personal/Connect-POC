/*

CREATE TABLE [Offices] (
    [Office_Id] [int] IDENTITY(1, 1) NOT NULL,
    [Office_Name] [nvarchar](200) NOT NULL,
    [Office_Location] [geography] NOT NULL,
    [Update_By] nvarchar(30) NULL,
    [Update_Time] [datetime]
) ON [PRIMARY]

GO

INSERT INTO [dbo].[Offices] VALUES ('Microsoft Zurich', 'POINT(8.590847 47.408860 )', 'mike', GetDate())
INSERT INTO [dbo].[Offices] VALUES ('Microsoft San Francisco', 'POINT(-122.403697 37.792062 )', 'mike', GetDate())
INSERT INTO [dbo].[Offices] VALUES ('Microsoft Paris', 'POINT(2.265509 48.833946)', 'mike', GetDate())
INSERT INTO [dbo].[Offices] VALUES ('Microsoft Sydney', 'POINT(151.138378 -33.796572)', 'mike', GetDate())
INSERT INTO [dbo].[Offices] VALUES ('Microsoft Dubai', 'POINT(55.286282 25.228850)', 'mike', GetDate())
*/


DECLARE 
    @latitude numeric(12, 7),
    @longitude numeric(12, 7)

-- enter your current location's latitude and longitude. You can find your current location details using https://www.maps.ie/coordinates.html
SET @latitude =  19.0058555
SET @longitude = 72.8256794

DECLARE @g geography = 'POINT(' + cast(@longitude as nvarchar) + ' ' + cast(@latitude as nvarchar) + ')';

SELECT [Office_Name], 
       cast([Office_Location].STDistance(@g) / 1609.344 as numeric(10, 1)) as 'Distance (in miles)' 
FROM [Offices]
ORDER BY 2 ASC

select * from [dbo].[Offices]