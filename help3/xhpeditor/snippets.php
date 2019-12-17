<?php
function display_xml_error($error, $xml)
{
    $return  = '<p>'.$xml[$error->line - 1] . '<br>';
//     $return .= str_repeat('-', $error->column) . "^<br>";

    switch ($error->level) {
        case LIBXML_ERR_WARNING:
            $return .= "Warning  $error->code: ";
            break;
         case LIBXML_ERR_ERROR:
            $return .= "Error $error->code: ";
            break;
        case LIBXML_ERR_FATAL:
            $return .= "Fatal Error $error->code: ";
            break;
    }

    $return .= trim($error->message) .
               "<br>  Line: $error->line" .
               "<br>  Column: $error->column";

    if ($error->file) {
        $return .= "<br>  File: " . $error->file;
    }

    return $return . "<br>--------------------------------------------</p>";
}
?>
